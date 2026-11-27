"""Validação interna por grupos para explorar FedProx sem avaliar o teste global."""

import argparse
import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np
import torch

import experimentar_fedprox as prox
import prever_suporte_clientes as agrupamento
import treinar_cnn as base
from avaliar_clientes import medir_fatia
from avaliar_corrigido import ler_sexta, padronizar, sha256
from avaliar_piloto import chaves_vetores
from cnn1d import CNN1D


def json_ler(caminho):
    return json.loads(caminho.read_bytes())


def hash_indices(indices):
    return prox.hash_array(indices.astype("<i8"))


def ler_dados(pasta, protocolo):
    arquivo = pasta / "CICIDS2017_improved.zip"
    assert sha256(arquivo) == protocolo["zip_sha256"]
    assert sha256(pasta / "split_cronologico.npz") == protocolo["split_global_sha256"]
    return ler_sexta(arquivo)


def intersecoes(dados, treino, validacao):
    return {
        "linhas": int(np.intersect1d(treino, validacao).size),
        "grupos": int(np.intersect1d(dados.grupos[treino], dados.grupos[validacao]).size),
        "vetores_brutos": int(np.intersect1d(chaves_vetores(dados.x[treino]),
                                             chaves_vetores(dados.x[validacao])).size),
    }


def preparar(pasta, protocolo_path, saida):
    protocolo = json_ler(protocolo_path)
    saida.mkdir(parents=True, exist_ok=False)
    base.escrever_json(saida / "protocolo.json", protocolo)
    dados = ler_dados(pasta, protocolo)
    with np.load(pasta / "split_cronologico.npz", allow_pickle=False) as manifesto:
        treino_anterior, teste = [np.flatnonzero(np.isin(dados.linhas, manifesto[k]))
                                  for k in ("linhas_treino", "linhas_teste")]
        assert dados.colunas == manifesto["ordem_features"].tolist()
    # Reproduz apenas o expurgo histórico que define o pool original, sem inferência no teste.
    pool, _, _, historico = padronizar(dados, treino_anterior, teste)
    assert hash_indices(dados.linhas[pool]) == protocolo["pool_treino_original_sha256"]
    assert historico == [{"vetores_em_comum": 10, "treino_removido": {"BENIGN": 29, "DDoS": 0}}]
    blocos = agrupamento.blocos_indivisiveis(dados.grupos[pool], dados.x[pool])
    fracao = protocolo["fracao_validacao_por_classe_alvo"]
    with patch.object(agrupamento, "SEED", protocolo["seed_validacao"]):
        partes, _ = agrupamento.repartir(blocos, dados.y[pool], np.array([[1-fracao]*2, [fracao]*2]))
    ajuste_inicial, validacao = pool[partes[0]], pool[partes[1]]
    assert np.array_equal(np.sort(np.concatenate((ajuste_inicial, validacao))), pool)
    assert not any(intersecoes(dados, ajuste_inicial, validacao).values())
    # A validação é mantida fixa se a precisão da transformação gerar novas colisões.
    ajuste, x, xv, ajustes = padronizar(dados, ajuste_inicial, validacao)
    x32, xv32 = x.astype(np.float32), xv.astype(np.float32)
    removidos = []
    while True:
        chaves = chaves_vetores(x32)
        comuns = np.intersect1d(chaves, chaves_vetores(xv32))
        if not len(comuns):
            break
        colisao = np.isin(chaves, comuns)
        removidos.append(base.piloto.contar_classes(dados.y[ajuste[colisao]]))
        ajuste, x, xv, novos = padronizar(dados, ajuste[~colisao], validacao)
        ajustes.extend(novos)
        x32, xv32 = x.astype(np.float32), xv.astype(np.float32)
    assert set(dados.y[ajuste]) == set(dados.y[validacao]) == {0, 1}
    assert not any(intersecoes(dados, ajuste, validacao).values())
    assert not np.intersect1d(dados.grupos[pool], dados.grupos[teste]).size
    excluidos = np.setdiff1d(pool, np.concatenate((ajuste, validacao)))
    assert np.array_equal(np.sort(np.concatenate((ajuste, validacao, excluidos))), pool)
    manifesto = {
        "protocolo_sha256": sha256(saida / "protocolo.json"), "pool_sha256": protocolo["pool_treino_original_sha256"],
        "split_global_sha256": protocolo["split_global_sha256"], "ordem_features": dados.colunas,
        "pool_original": dados.linhas[pool], "ajuste": dados.linhas[ajuste],
        "validacao": dados.linhas[validacao], "excluidos": dados.linhas[excluidos],
    }
    with (saida / "manifesto_validacao.npz").open("xb") as arquivo:
        np.savez_compressed(arquivo, **manifesto)
    auditoria = {
        "pool": base.piloto.contar_classes(dados.y[pool]),
        "ajuste": base.piloto.contar_classes(dados.y[ajuste]),
        "validacao": base.piloto.contar_classes(dados.y[validacao]),
        "excluidos_do_ajuste": base.piloto.contar_classes(dados.y[excluidos]),
        "expurgo_historico": historico, "colisoes_float64": ajustes, "colisoes_float32": removidos,
        "grupos_pool": int(np.unique(dados.grupos[pool]).size), "blocos_pool": len(blocos),
        "intersecoes_ajuste_validacao": intersecoes(dados, ajuste, validacao),
        "grupos_compartilhados_pool_teste": 0, "vetores_float32_ajuste_validacao": 0,
        "ajuste_sha256": hash_indices(dados.linhas[ajuste]),
        "validacao_sha256": hash_indices(dados.linhas[validacao]),
        "manifesto_sha256": sha256(saida / "manifesto_validacao.npz"),
    }
    base.escrever_json(saida / "auditoria.json", auditoria)
    print(json.dumps(auditoria, indent=2, ensure_ascii=False))


def carregar_ajuste_validacao(pasta, particao):
    protocolo = json_ler(particao / "protocolo.json")
    auditoria = json_ler(particao / "auditoria.json")
    assert sha256(particao / "manifesto_validacao.npz") == auditoria["manifesto_sha256"]
    dados = ler_dados(pasta, protocolo)
    with np.load(particao / "manifesto_validacao.npz", allow_pickle=False) as manifesto:
        assert sha256(particao / "protocolo.json") == manifesto["protocolo_sha256"].item()
        assert hash_indices(manifesto["pool_original"]) == protocolo["pool_treino_original_sha256"]
        assert np.array_equal(np.sort(np.concatenate([manifesto[k] for k in ("ajuste", "validacao", "excluidos")])),
                              manifesto["pool_original"])
        ajuste, validacao = [np.flatnonzero(np.isin(dados.linhas, manifesto[k])) for k in ("ajuste", "validacao")]
        assert np.array_equal(dados.linhas[ajuste], manifesto["ajuste"])
        assert np.array_equal(dados.linhas[validacao], manifesto["validacao"])
        assert dados.colunas == manifesto["ordem_features"].tolist()
    assert not any(intersecoes(dados, ajuste, validacao).values())
    bruto = dados.x[ajuste]
    media, escala = bruto.mean(axis=0), bruto.std(axis=0)
    escala[escala == 0] = 1.0
    x, xv = [((dados.x[idx] - media) / escala).astype(np.float32) for idx in (ajuste, validacao)]
    assert np.isfinite(x).all() and np.isfinite(xv).all()
    assert not np.intersect1d(chaves_vetores(x), chaves_vetores(xv)).size
    assert hash_indices(dados.linhas[ajuste]) == auditoria["ajuste_sha256"]
    assert hash_indices(dados.linhas[validacao]) == auditoria["validacao_sha256"]
    return protocolo, auditoria, dados.colunas, x, xv, dados.y[ajuste], dados.y[validacao], media, escala


def calibrar(scores, rotulos, fpr_maxima):
    assert np.isfinite(scores).all() and set(rotulos) == {0, 1}
    suporte_benign = int(np.count_nonzero(rotulos == 0))
    orcamento_fp = int(np.floor(fpr_maxima * suporte_benign))
    unicos, grupos = np.unique(scores, return_inverse=True)
    fp = np.cumsum(np.bincount(grupos[rotulos == 0], minlength=len(unicos))[::-1])
    vp = np.cumsum(np.bincount(grupos[rotulos == 1], minlength=len(unicos))[::-1])
    limiares = np.concatenate(([np.nextafter(float(unicos[-1]), np.inf)], unicos[::-1].astype(np.float64)))
    fp, vp = np.concatenate(([0], fp)), np.concatenate(([0], vp))
    aptos = np.flatnonzero(fp <= orcamento_fp)
    melhor = min(aptos, key=lambda i: (-vp[i], fp[i], -limiares[i]))
    limiar = float(limiares[melhor])
    resultado = medir_fatia(rotulos, scores.astype(np.float64) >= limiar)
    assert resultado["fpr"] <= fpr_maxima and resultado["matriz_real_por_previsto"][0][1] == fp[melhor]
    return {"limiar": limiar, "orcamento_fp": orcamento_fp, **resultado}


def conferir_calibracao():
    scores = np.array([0.8, 0.4, 0.9, 0.8, 0.3], dtype=np.float64)
    y = np.array([0, 0, 1, 1, 1])
    a, b = calibrar(scores, y, 0.0), calibrar(scores, y, 0.5)
    assert a["limiar"] == 0.9 and a["matriz_real_por_previsto"] == [[2, 0], [2, 1]]
    assert b["limiar"] == 0.8 and b["matriz_real_por_previsto"] == [[1, 1], [1, 2]]
    # O empate em 0.8 inclui os dois rótulos, respeitando a regra score >= limiar.
    return {"sem_fp": a, "um_fp": b}


def treinar(pasta, particao, saida):
    inicio = perf_counter()
    saida.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    protocolo, audit, colunas, x, xv, y, yv, media, escala = carregar_ajuste_validacao(pasta, particao)
    base.escrever_json(saida / "teste_calibracao.json", conferir_calibracao())
    with patch.object(base.piloto, "CLIENTES", base.CLIENTES):
        clientes, tentativa = base.distribuir_dirichlet(y, protocolo["seed_clientes"])
    assert np.array_equal(np.sort(np.concatenate(clientes)), np.arange(len(y)))
    torch.manual_seed(protocolo["seed_modelo"])
    modelo = CNN1D()
    inicial = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
    contrato = {
        "formato": "secfednet-cnn1d-v1", "ordem_features": colunas,
        "classes": {"0": "BENIGN", "1": "DDoS"}, "limiar": 0.5,
        "normalizacao": "media e desvio ddof=0 somente no subconjunto de ajuste, escala constante vira 1",
        "manifesto_validacao_sha256": audit["manifesto_sha256"],
        "ajuste_sha256": audit["ajuste_sha256"], "validacao_sha256": audit["validacao_sha256"],
    }
    grade = tuple((e["nome"], e["mu"]) for e in protocolo["grade"])
    assert protocolo["rodadas"] == prox.RODADAS == 3
    assert protocolo["seed_modelo"] == base.SEED_MODELO and protocolo["seed_clientes"] == base.SEED_PARTICAO
    assert protocolo["alpha_clientes"] == base.ALFA_DIRICHLET
    with patch.object(prox, "ENSAIOS", grade):
        config = prox.configuracao(clientes, y, contrato, modelo, tentativa)
    config.pop("tolerancia_mu0")
    config["selecao_mu"] = "apenas recall calibrado na validacao dentro do teto de FPR do protocolo"
    config["protocolo"] = protocolo
    config["protocolo_sha256"] = sha256(particao / "protocolo.json")
    base.escrever_json(saida / "configuracao.json", config)
    torch.save(inicial, saida / "pesos_iniciais.pt")
    print("Configuração fixada. Iniciando os treinos pareados.", flush=True)
    treinos = {}
    for nome, mu in grade:
        treinos[nome] = prox.treinar_metodo(nome, mu, inicial, x, y, clientes, config, saida,
                                          torch.from_numpy(media), torch.from_numpy(escala))
        base.escrever_json(saida / nome / "treino.json", treinos[nome])
        print(f"{nome}: treino concluído.", flush=True)

    resultados = []
    for nome, mu in grade:
        caminho = saida / nome / "checkpoint.pt"
        assert sha256(caminho) == treinos[nome]["checkpoint_sha256"]
        checkpoint = torch.load(caminho, map_location="cpu", weights_only=True)
        assert checkpoint["contrato"] == contrato
        assert np.array_equal(checkpoint["media"].numpy(), media) and np.array_equal(checkpoint["escala"].numpy(), escala)
        modelo.load_state_dict(checkpoint["state_dict"])
        modelo.eval()
        with torch.inference_mode():
            scores = torch.cat([torch.sigmoid(modelo(lote)[0])
                                for lote in torch.from_numpy(xv).split(base.LOTE)]).numpy()
        np.save(saida / nome / "scores_validacao.npy", scores, allow_pickle=False)
        resultado = {"nome": nome, "mu": mu,
                     "limiar_05": medir_fatia(yv, scores >= 0.5),
                     "calibrado": calibrar(scores, yv, protocolo["fpr_maxima_validacao"])}
        base.escrever_json(saida / nome / "validacao.json", resultado)
        resultados.append(resultado)
    melhor = min(resultados, key=lambda r: (-r["calibrado"]["recall_ddos"], r["calibrado"]["fpr"], r["mu"] or 0.0))
    base.escrever_json(saida / "selecao.json", {
        "uso": "selecao exploratoria na mesma validacao usada para escolher o limiar",
        "avaliou_teste_global": False, "escolhido": melhor["nome"], "mu": melhor["mu"],
        "limiar": melhor["calibrado"]["limiar"], "teto_fpr": protocolo["fpr_maxima_validacao"],
        "manifesto_sha256": audit["manifesto_sha256"], "resultados": resultados,
        "tempo_total_s": perf_counter() - inicio,
    })
    print(json.dumps({"escolhido": melhor["nome"], "resultados": resultados}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    comandos = parser.add_subparsers(dest="etapa", required=True)
    for nome in ("preparar", "treinar"):
        sub = comandos.add_parser(nome)
        sub.add_argument("dados", type=Path)
        sub.add_argument("entrada", type=Path)
        sub.add_argument("saida", type=Path)
    args = parser.parse_args()
    if args.etapa == "preparar":
        preparar(args.dados, args.entrada, args.saida)
    else:
        treinar(args.dados, args.entrada, args.saida)


if __name__ == "__main__":
    main()
