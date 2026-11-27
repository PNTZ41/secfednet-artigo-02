"""Extensão de 20 rodadas do piloto de 12h37, sem editar suas fontes/saídas."""

import argparse
import csv
import json
import platform
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np
import torch

import experimentar_scaffold as piloto
from scaffold import arrays_modelo, carregar_modelo, hash_arrays, ler_estado, ordem_minibatches

LOCAL = piloto.LOCAL
ANTERIOR = LOCAL / "cnn-scaffold/ensaio-01/execucao"
PROTOCOLO = Path(__file__).with_name("protocolo_20.json")


@torch.inference_mode()
def inferir(modelo, x, y, lote):
    modelo.eval()
    logits = torch.cat([modelo(l)[0] for l in torch.from_numpy(x).split(lote)])
    perdas = torch.nn.functional.binary_cross_entropy_with_logits(
        logits, torch.from_numpy(y.astype(np.float32)), reduction="none").numpy()
    return torch.sigmoid(logits).numpy(), perdas.astype(np.float64)


def salvar_curva(saida, curva):
    piloto.base.escrever_json(saida / "curva.json", curva)
    campos = ["rodada", "perda_treino_global_uniforme_clientes", "perda_treino_global_por_exemplo",
              "perda_online_uniforme_clientes", "perda_online_por_exemplo", "recall_ddos", "fp", "fpr",
              "macro_f1", "limiar", "bytes_parametros_acumulados", "bytes_controles_acumulados",
              "bytes_brutos_acumulados", "passos_acumulados", "exposicoes_acumuladas"]
    with (saida / "curva.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in curva:
            v = r["validacao_calibrada"]
            writer.writerow({k: ({"recall_ddos": v["recall_ddos"], "fp": v["matriz_real_por_previsto"][0][1],
                                  "fpr": v["fpr"], "macro_f1": v["macro_f1_binario"], "limiar": v["limiar"]}.get(k)
                                 if k in ("recall_ddos", "fp", "fpr", "macro_f1", "limiar") else r[k])
                             for k in campos})


class EstrategiaCurva(piloto.Estrategia):
    def __init__(self, *args, x, y, xv, yv, partes, **kwargs):
        super().__init__(*args, **kwargs)
        self.x, self.y, self.xv, self.yv, self.partes = x, y, xv, yv, partes
        self.modelo_avaliacao = piloto.CNN1D()
        self.curva = []

    def aggregate_fit(self, server_round, results, failures):
        retorno = super().aggregate_fit(server_round, results, failures)
        inicio = perf_counter()
        carregar_modelo(self.modelo_avaliacao, self.pesos)
        _, perdas = inferir(self.modelo_avaliacao, self.x, self.y, self.config["lote"])
        scores, _ = inferir(self.modelo_avaliacao, self.xv, self.yv, self.config["lote"])
        np.save(self.saida / f"scores_validacao_{server_round:02d}.npy", scores, allow_pickle=False)
        evidencia = self.rodadas[-1]
        pesos_bytes = evidencia["bytes_parametros_recebidos"] + evidencia["bytes_parametros_enviados"]
        controles_bytes = evidencia["bytes_controles_recebidos"] + evidencia["bytes_controles_enviados"]
        anterior = self.curva[-1] if self.curva else {
            "bytes_parametros_acumulados": 0, "bytes_controles_acumulados": 0,
            "passos_acumulados": 0, "exposicoes_acumuladas": 0}
        linha = {"rodada": server_round,
                 "perda_treino_global_uniforme_clientes": float(np.mean([perdas[idx].mean() for idx in self.partes])),
                 "perda_treino_global_por_exemplo": float(perdas.mean()),
                 "perda_online_uniforme_clientes": float(np.mean([c["perda"] for c in evidencia["clientes"]])),
                 "perda_online_por_exemplo": sum(c["exemplos"] * c["perda"] for c in evidencia["clientes"]) / len(self.y),
                 "validacao_calibrada": piloto.validacao.calibrar(scores, self.yv, self.config["fpr_maxima_validacao"]),
                 "validacao_limiar_05": piloto.validacao.medir_fatia(self.yv, scores >= 0.5),
                 "scores_sha256": piloto.sha256(self.saida / f"scores_validacao_{server_round:02d}.npy"),
                 "pesos_sha256": hash_arrays(self.pesos),
                 "bytes_parametros_acumulados": anterior["bytes_parametros_acumulados"] + pesos_bytes,
                 "bytes_controles_acumulados": anterior["bytes_controles_acumulados"] + controles_bytes,
                 "passos_acumulados": anterior["passos_acumulados"] + evidencia["passos"],
                 "exposicoes_acumuladas": anterior["exposicoes_acumuladas"] + evidencia["exemplos"],
                 "tempo_monitoramento_s": perf_counter() - inicio}
        linha["bytes_brutos_acumulados"] = linha["bytes_parametros_acumulados"] + linha["bytes_controles_acumulados"]
        self.curva.append(linha)
        salvar_curva(self.saida, self.curva)
        v = linha["validacao_calibrada"]
        print(f"{'SCAFFOLD' if self.scaffold else 'FedAvg-SGD'} r={server_round:02d} "
              f"BCE_global={linha['perda_treino_global_uniforme_clientes']:.6f} "
              f"recall={v['recall_ddos']:.6f} FP={v['matriz_real_por_previsto'][0][1]} "
              f"FPR={v['fpr']:.6f} bytes={linha['bytes_brutos_acumulados']}", flush=True)
        return retorno


def carregar_dados():
    return piloto.validacao.carregar_ajuste_validacao(LOCAL / "cicids2017-corrigido", piloto.PARTICAO)


def treinar(saida):
    inicio = perf_counter()
    saida.mkdir(parents=True, exist_ok=False)
    config = piloto.ler_json(PROTOCOLO)
    antigo = piloto.ler_json(ANTERIOR / "configuracao.json")
    protocolo_antigo = piloto.ler_json(Path(__file__).with_name("protocolo.json"))
    for k, v in protocolo_antigo.items():
        if k not in ("formato", "rodadas"):
            assert config[k] == v, k
    assert config["rodadas"] == 20 and antigo["rodadas"] == 2
    _, audit, colunas, x, xv, y, yv, media, escala = carregar_dados()
    assert config["manifesto_validacao_sha256"] == audit["manifesto_sha256"]
    assert colunas == antigo["contrato"]["ordem_features"]
    assert hash_arrays([media]) == antigo["normalizacao_media_sha256"]
    assert hash_arrays([escala]) == antigo["normalizacao_escala_sha256"]
    with patch.object(piloto.base.piloto, "CLIENTES", 5):
        partes, tentativa = piloto.base.distribuir_dirichlet(y, config["seed_clientes"])
    assert tentativa == antigo["tentativa_particao"]
    assert np.array_equal(np.sort(np.concatenate(partes)), np.arange(len(y)))
    with np.load(ANTERIOR / "clientes.npz", allow_pickle=False) as manifesto:
        assert all(np.array_equal(a, manifesto[f"cliente_{i}"]) for i, a in enumerate(partes))
    torch.manual_seed(config["seed_modelo"])
    iniciais = arrays_modelo(piloto.CNN1D())
    assert hash_arrays(iniciais) == antigo["pesos_iniciais_sha256"]
    ordens = [{"rodada": r, "cliente": i, "seed": config["seed_modelo"] + 100 * r + i,
               "ordem_sha256": hash_arrays([ordem_minibatches(len(idx), config["seed_modelo"] + 100 * r + i)
                                             .numpy().astype("<i8")]),
               "passos": (len(idx) + config["lote"] - 1) // config["lote"]}
              for r in range(1, 21) for i, idx in enumerate(partes)]
    assert ordens[:len(antigo["minibatches"])] == antigo["minibatches"]
    contrato = antigo["contrato"]
    np.savez_compressed(saida / "clientes.npz", **{f"cliente_{i}": idx for i, idx in enumerate(partes)})
    config.update({"particoes": antigo["particoes"], "minibatches": ordens,
                   "tentativa_particao": tentativa, "pesos_iniciais_sha256": hash_arrays(iniciais),
                   "contrato": contrato, "auditoria_reutilizada": audit,
                   "normalizacao_media_sha256": hash_arrays([media]), "normalizacao_escala_sha256": hash_arrays([escala]),
                   "clientes_npz_sha256": piloto.sha256(saida / "clientes.npz"),
                   "configuracao_12h37_sha256": piloto.sha256(ANTERIOR / "configuracao.json"),
                   "protocolo_20_sha256": piloto.sha256(PROTOCOLO),
                   "exemplos_por_rodada": len(y), "exposicoes_por_metodo": len(y) * 20,
                   "passos_por_metodo": sum(o["passos"] for o in ordens),
                   "torch_threads": 2, "torch_interop_threads": 1, "deterministico": True,
                   "versoes": {"python": platform.python_version(), "torch": str(torch.__version__),
                                "flower": piloto.flwr.__version__, "numpy": np.__version__, "plataforma": platform.platform()},
                   "fontes_20_sha256": piloto.sha256(Path(__file__).with_name("SHA256_FONTES_20"))})
    piloto.base.escrever_json(saida / "configuracao.json", config)
    torch.save([torch.from_numpy(a.copy()) for a in iniciais], saida / "pesos_iniciais.pt")
    print("Protocolo e configuração fixados antes de treinar; 20 rodadas completas por método.", flush=True)
    def fabrica(*args, **kwargs):
        return EstrategiaCurva(*args, x=x, y=y, xv=xv, yv=yv, partes=partes, **kwargs)
    treinos = []
    with patch.object(piloto, "Estrategia", fabrica):
        for nome in config["metodos"]:
            treinos.append(piloto.treinar_metodo(nome, iniciais, x, y, partes, config, saida / nome,
                                               contrato, media, escala))
    for t in treinos:
        efetivas = [{k: cl[k] for k in ("rodada", "cliente", "seed", "ordem_sha256", "passos")}
                    for r in t["rodadas"] for cl in r["clientes"]]
        assert efetivas == ordens
        antigo_treino = piloto.ler_json(ANTERIOR / t["nome"] / "treino.json")
        for nova, anterior in zip(t["rodadas"][:2], antigo_treino["rodadas"], strict=True):
            assert nova["pesos_sha256"] == anterior["pesos_sha256"]
            assert nova["c_sha256"] == anterior["c_sha256"]
            for nc, ac in zip(nova["clientes"], anterior["clientes"], strict=True):
                assert nc["ci_final_sha256"] == ac["ci_final_sha256"]
        assert np.array_equal(np.load(saida / t["nome"] / "scores_validacao_02.npy", allow_pickle=False),
                              np.load(ANTERIOR / t["nome"] / "scores_validacao.npy", allow_pickle=False))
    assert treinos[0]["rodadas"][0]["pesos_sha256"] == treinos[1]["rodadas"][0]["pesos_sha256"]
    piloto.base.escrever_json(saida / "pareamento.json", {
        "inicializacao_particoes_normalizacao_minibatches_iguais": True,
        "duas_primeiras_rodadas_reproduzem_pesos_e_controles_12h37_bit_a_bit": True,
        "scores_da_rodada_2_reproduzem_12h37_bit_a_bit": True,
        "tolerancia_igualdade": 0.0, "passos_por_metodo": config["passos_por_metodo"],
        "avaliou_teste_global": False})
    piloto.avaliar(saida, dados=(xv, yv, media, escala))
    comparar(saida)
    piloto.base.escrever_json(saida / "tempo.json", {"total_s": perf_counter() - inicio})


def comparar(saida):
    curvas = {n: piloto.ler_json(saida / n / "curva.json") for n in ("fedavg_sgd", "scaffold")}
    def ponto(nome, r):
        linha = curvas[nome][r - 1]
        assert linha["rodada"] == r
        return {"metodo": nome, **linha}
    pares = [{"eixo": "rodadas", "fedavg": ponto("fedavg_sgd", 20), "scaffold": ponto("scaffold", 20)},
             {"eixo": "bytes_brutos", "fedavg": ponto("fedavg_sgd", 20), "scaffold": ponto("scaffold", 10)}]
    assert pares[1]["fedavg"]["bytes_brutos_acumulados"] == pares[1]["scaffold"]["bytes_brutos_acumulados"] == 919200
    for p in pares:
        a, b = p["fedavg"]["validacao_calibrada"], p["scaffold"]["validacao_calibrada"]
        p["delta_scaffold_menos_fedavg"] = {"recall_ddos": b["recall_ddos"] - a["recall_ddos"],
                                          "fpr": b["fpr"] - a["fpr"],
                                          "fp": b["matriz_real_por_previsto"][0][1] - a["matriz_real_por_previsto"][0][1]}
    piloto.base.escrever_json(saida / "comparacoes.json", {"avaliou_teste_global": False, "pares": pares})
    with (saida / "curvas.csv").open("w", encoding="utf-8", newline="") as arquivo:
        linhas = []
        for nome in curvas:
            with (saida / nome / "curva.csv").open(encoding="utf-8", newline="") as f:
                linhas += [{"metodo": nome, **r} for r in csv.DictReader(f)]
        writer = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        writer.writeheader()
        writer.writerows(linhas)


def verificar(saida):
    _, audit, _, _, xv, _, yv, media, escala = carregar_dados()
    config = piloto.ler_json(saida / "configuracao.json")
    assert audit["manifesto_sha256"] == config["manifesto_validacao_sha256"]
    piloto.avaliar(saida, dados=(xv, yv, media, escala))
    for nome in config["metodos"]:
        curva = piloto.ler_json(saida / nome / "curva.json")
        treinos = piloto.ler_json(saida / nome / "treino.json")["rodadas"]
        assert len(curva) == len(treinos) == 20
        modelo = piloto.CNN1D()
        for r, t in zip(curva, treinos, strict=True):
            path = saida / nome / f"rodada-{r['rodada']:02d}.pt"
            assert piloto.sha256(path) == t["estado_sha256"]
            numero, pesos, cg, cis = ler_estado(path)
            assert numero == r["rodada"]
            assert hash_arrays(pesos) == r["pesos_sha256"]
            assert hash_arrays(cg) == t["c_sha256"]
            assert all(hash_arrays(ci) == c["ci_final_sha256"] for ci, c in zip(cis, t["clientes"], strict=True))
            carregar_modelo(modelo, pesos)
            scores, _ = inferir(modelo, xv, yv, config["lote"])
            arquivo = saida / nome / f"scores_validacao_{numero:02d}.npy"
            assert piloto.sha256(arquivo) == r["scores_sha256"]
            assert np.array_equal(scores, np.load(arquivo, allow_pickle=False))
            assert piloto.validacao.calibrar(scores, yv, config["fpr_maxima_validacao"]) == r["validacao_calibrada"]
            cm = np.array(r["validacao_calibrada"]["matriz_real_por_previsto"])
            assert cm.sum(axis=1).tolist() == [40776, 10039]
        print(nome, ": 20 estados, controles, scores e métricas recarregados e conferidos.", flush=True)
    piloto.base.escrever_json(saida / "verificacao_independente.json", {
        "outro_processo": True, "estados_verificados": 40, "scores_iguais_bit_a_bit": True,
        "controles_e_hashes_conferidos": True, "matrizes_suporte_reconciliadas": True,
        "torch_load_weights_only": True, "avaliou_teste_global": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=("treinar", "verificar"))
    parser.add_argument("saida", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    (treinar if args.acao == "treinar" else verificar)(args.saida)
