"""Congela a prévia da seed 2405 e avalia a CNN no teste cronológico por cliente."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from avaliar_corrigido import ler_sexta, padronizar, sha256
from avaliar_piloto import chaves_vetores
from cnn1d import CNN1D
from piloto_fedavg import CLASSES, contar_classes
from prever_suporte_clientes import SEED, blocos_indivisiveis, repartir


MATRIZ_GLOBAL = [[24886, 7], [28, 20140]]
LOTE = 512


def exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def hash_linhas(linhas):
    return hashlib.sha256(linhas.astype("<i8").tobytes()).hexdigest()


def congelar_e_ler(caminho, manifesto):
    if not caminho.exists():
        with caminho.open("xb") as arquivo:
            np.savez_compressed(arquivo, **manifesto)
    with np.load(caminho, allow_pickle=False) as congelado:
        exigir(set(congelado.files) == set(manifesto), "Campos do manifesto não coincidem")
        for chave, valor in manifesto.items():
            exigir(np.array_equal(congelado[chave], valor), f"Manifesto divergente em {chave}")
        return [congelado[f"cliente_{i}"] for i in range(5)]


def medir_fatia(y, previsto):
    matriz = np.bincount(2 * y + previsto, minlength=4).reshape(2, 2)
    (vn, fp), (fn, vp) = matriz.tolist()
    benign, ddos = vn + fp, vp + fn
    return {
        "suporte": {"BENIGN": benign, "DDoS": ddos},
        "matriz_real_por_previsto": matriz.tolist(),
        "fpr": fp / benign if benign else "NA",
        "recall_ddos": vp / ddos if ddos else "NA",
        "macro_f1_binario": (2 * vn / (2 * vn + fp + fn) + 2 * vp / (2 * vp + fp + fn)) / 2
        if benign and ddos else "NA",
    }


def avaliar(dados_dir, piloto, previa_path, manifesto_path):
    pasta = piloto / "artefatos"
    contrato = json.loads((pasta / "contrato.json").read_bytes())
    referencia = json.loads((pasta / "metricas.json").read_bytes())
    exigir(referencia["metricas"]["matriz_real_por_previsto"] == MATRIZ_GLOBAL,
           "A matriz registrada no piloto diverge da referência")
    particao = json.loads((pasta / "particao.json").read_bytes())
    previa = json.loads(previa_path.read_bytes())
    caminho_zip = dados_dir / "CICIDS2017_improved.zip"
    caminho_split = dados_dir / "split_cronologico.npz"
    caminho_checkpoint = pasta / "checkpoint_cnn1d.pt"
    hash_checkpoint = sha256(caminho_checkpoint)
    exigir(hash_checkpoint == referencia["checkpoint_sha256"], "SHA-256 do checkpoint divergente")
    exigir(sha256(caminho_zip) == contrato["zip_sha256"], "SHA-256 do ZIP divergente")
    exigir(sha256(caminho_split) == contrato["split_sha256"] == previa["split_sha256"],
           "SHA-256 do teste cronológico divergente")
    exigir(SEED == previa["seed"] == 2405, "Seed da prévia divergente")
    checkpoint = torch.load(caminho_checkpoint, map_location="cpu", weights_only=True)
    exigir(checkpoint["contrato"] == contrato, "Contrato do checkpoint divergente")

    dados = ler_sexta(caminho_zip)
    with np.load(caminho_split, allow_pickle=False) as global_split:
        treino, teste = [np.flatnonzero(np.isin(dados.linhas, global_split[k]))
                         for k in ("linhas_treino", "linhas_teste")]
        exigir(np.array_equal(dados.linhas[treino], global_split["linhas_treino"]), "Índices de treino divergentes")
        exigir(np.array_equal(dados.linhas[teste], global_split["linhas_teste"]), "Índices de teste divergentes")
        exigir(dados.colunas == global_split["ordem_features"].tolist() == contrato["ordem_features"],
               "Ordem das features divergente")
        corte = global_split["corte_utc_us"].item()
    exigir(np.all(dados.tempos[treino] < corte) and np.all(dados.tempos[teste] >= corte),
           "Partição fora do corte cronológico")
    treino, x_treino, x_teste, ajustes = padronizar(dados, treino, teste)
    exigir(ajustes == contrato["expurgo_apos_padronizacao"], "Expurgo do treino divergente")
    hash_treino = hash_linhas(dados.linhas[treino])
    exigir(hash_treino == contrato["linhas_treino_final_sha256"], "SHA-256 do treino final divergente")
    exigir(not np.intersect1d(treino, teste).size, "Treino e teste compartilham linhas")
    grupos_teste = dados.grupos[teste]
    exigir(not np.intersect1d(dados.grupos[treino], grupos_teste).size, "Treino e teste compartilham grupos")
    treino_bruto = dados.x[treino]
    media, escala = treino_bruto.mean(axis=0), treino_bruto.std(axis=0)
    escala[escala == 0.0] = 1.0
    del treino_bruto
    exigir(np.array_equal(media, checkpoint["media"].numpy())
           and np.array_equal(escala, checkpoint["escala"].numpy()), "Normalização não coincide com o treino final")
    x = ((dados.x[teste] - media) / escala).astype(np.float32)
    exigir(np.array_equal(x, x_teste.astype(np.float32)), "Pré-processamento do checkpoint divergente")
    chaves = chaves_vetores(x)
    exigir(not np.intersect1d(chaves_vetores(x_treino.astype(np.float32)), chaves).size,
           "Treino e teste compartilham vetores em float32")
    y = dados.y[teste]

    suporte = np.array([[c[classe] for classe in CLASSES] for c in particao["contagens_clientes"]])
    blocos = blocos_indivisiveis(grupos_teste, x)
    propostas, _ = repartir(blocos, y, suporte)
    exigir(len(propostas) == len(previa["clientes"]) == 5, "Número de fatias divergente")
    exigir(np.array_equal(np.sort(np.concatenate(propostas)), np.arange(len(teste))),
           "As fatias não cobrem o teste global exatamente uma vez")
    linhas = dados.linhas[teste]
    vistos_grupos, vistos_vetores = set(), set()
    manifesto = {"formato": "secfednet-fatias-v1", "seed": SEED,
                 "split_global_sha256": contrato["split_sha256"], "checkpoint_sha256": hash_checkpoint,
                 "treino_final_sha256": hash_treino, "linhas_teste_global_sha256": hash_linhas(linhas)}
    for i, indices in enumerate(propostas):
        esperado = previa["clientes"][i]
        ordinais = linhas[indices]
        grupos = set(grupos_teste[indices].tolist())
        vetores = {chave.tobytes() for chave in np.unique(chaves[indices])}
        exigir(esperado["cliente"] == i and hash_linhas(ordinais) == esperado["linhas_teste_sha256"],
               f"Índices do cliente {i} divergentes da prévia")
        exigir(contar_classes(y[indices]) == esperado["teste"], f"Suporte do cliente {i} divergente")
        exigir(not vistos_grupos & grupos and not vistos_vetores & vetores,
               f"A fatia {i} compartilha grupos ou vetores com outra fatia")
        vistos_grupos.update(grupos)
        vistos_vetores.update(vetores)
        manifesto[f"cliente_{i}"] = ordinais
    congelados = congelar_e_ler(manifesto_path, manifesto)

    torch.set_num_threads(2)
    modelo = CNN1D()
    modelo.load_state_dict(checkpoint["state_dict"])
    modelo.eval()
    with torch.inference_mode():
        previsto = torch.cat([torch.sigmoid(modelo(lote)[0]) >= contrato["limiar"]
                              for lote in torch.from_numpy(x).split(LOTE)]).numpy()
    clientes = []
    for i, ordinais in enumerate(congelados):
        idx = np.searchsorted(linhas, ordinais)
        clientes.append({"cliente": i, "linhas_teste_sha256": hash_linhas(ordinais),
                         **medir_fatia(y[idx], previsto[idx])})
    soma = np.sum([c["matriz_real_por_previsto"] for c in clientes], axis=0).tolist()
    resultado_global = medir_fatia(y, previsto)
    exigir(soma == resultado_global["matriz_real_por_previsto"] == MATRIZ_GLOBAL,
           "Soma das matrizes divergente do teste global")
    return {"escopo": "partições simuladas da mesma captura", "seed": SEED,
            "split_global_sha256": contrato["split_sha256"], "checkpoint_sha256": hash_checkpoint,
            "treino_final_sha256": hash_treino, "manifesto_fatias_sha256": sha256(manifesto_path),
            "auditoria": {"linhas_grupos_vetores_compartilhados_treino_teste": 0,
                          "grupos_vetores_compartilhados_entre_fatias": 0,
                          "grupos_no_teste": len(vistos_grupos), "blocos": len(blocos)},
            "clientes": clientes, "global": resultado_global, "soma_matrizes": soma}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dados_corrigidos", type=Path)
    parser.add_argument("piloto", type=Path)
    parser.add_argument("previa", type=Path)
    parser.add_argument("manifesto", type=Path)
    args = parser.parse_args()
    print(json.dumps(avaliar(args.dados_corrigidos, args.piloto, args.previa, args.manifesto),
                     ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
