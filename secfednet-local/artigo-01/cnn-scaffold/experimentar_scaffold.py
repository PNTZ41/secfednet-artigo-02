"""CNN-1D pareada: FedAvg-SGD e SCAFFOLD em Flower, só validação interna."""

import argparse
import json
import os
import platform
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

os.environ["FLWR_TELEMETRY_ENABLED"] = "0"

import flwr
import numpy as np
import torch
from flwr.client import NumPyClient
from flwr.common import ndarrays_to_parameters, parameters_to_ndarrays
from flwr.server import Server
from flwr.server.client_manager import SimpleClientManager
from flwr.server.strategy import FedAvg

import treinar_cnn as base
import validar_mu as validacao
from avaliar_corrigido import sha256
from cnn1d import CNN1D
from scaffold import (agregar, arrays_modelo, carregar_modelo, hash_arrays, ler_estado,
                      local_sgd, ordem_minibatches, salvar_estado, zeros)

RAIZ = Path(__file__).resolve().parents[3]
LOCAL = RAIZ / "secfednet-local/artigo-01"
PARTICAO = LOCAL / "cnn-validacao/particao"
PROTOCOLO = Path(__file__).with_name("protocolo.json")


def ler_json(p):
    return json.loads(p.read_bytes())


class ClienteSGD(NumPyClient):
    def __init__(self, cid, x, y, config, scaffold):
        self.cid, self.config, self.scaffold = cid, config, scaffold
        self.modelo = CNN1D()
        self.x, self.y = torch.from_numpy(x), torch.from_numpy(y.astype(np.float32))
        self.ci = zeros(arrays_modelo(self.modelo))
        self.registros = []

    def fit(self, payload, config):
        n = len(self.ci)
        assert len(payload) == n * (2 if self.scaffold else 1)
        globais = payload[:n]
        cg = payload[n:] if self.scaffold else zeros(globais)
        anterior_ci = hash_arrays(self.ci)
        rodada = int(config["rodada"])
        delta, novos_ci, dc, evid = local_sgd(
            self.modelo, self.x, self.y, globais, cg, self.ci, scaffold=self.scaffold,
            seed=self.config["seed_modelo"] + 100 * rodada + self.cid,
            lote=self.config["lote"], lr=self.config["lr"], perda_fn=torch.nn.BCEWithLogitsLoss())
        self.ci = novos_ci
        if self.registros:
            assert anterior_ci == self.registros[-1]["ci_final_sha256"]
        registro = {"rodada": rodada, "cliente": self.cid, **evid,
                    "pesos_recebidos_sha256": hash_arrays(globais),
                    "c_recebido_sha256": hash_arrays(cg),
                    "ci_inicial_sha256": anterior_ci, "ci_final_sha256": hash_arrays(self.ci),
                    "bytes_parametros_recebidos": sum(a.nbytes for a in globais),
                    "bytes_parametros_enviados": sum(a.nbytes for a in delta),
                    "bytes_controles_recebidos": sum(a.nbytes for a in cg) if self.scaffold else 0,
                    "bytes_controles_enviados": sum(a.nbytes for a in dc)}
        self.registros.append(registro)
        return delta + dc, len(self.y), {"perda": evid["perda"]}


class Estrategia(FedAvg):
    def __init__(self, iniciais, clientes, config, scaffold, saida):
        self.pesos, self.cg = [a.copy() for a in iniciais], zeros(iniciais)
        self.clientes, self.config, self.scaffold, self.saida = clientes, config, scaffold, saida
        self.rodadas = []
        super().__init__(fraction_fit=1.0, fraction_evaluate=0.0,
                         min_fit_clients=5, min_available_clients=5, min_evaluate_clients=5,
                         accept_failures=False, inplace=False,
                         on_fit_config_fn=lambda r: {"rodada": r},
                         initial_parameters=ndarrays_to_parameters(iniciais + (self.cg if scaffold else [])))
        salvar_estado(saida / "rodada-00.pt", 0, self.pesos, self.cg, [c.ci for c in clientes])

    def aggregate_fit(self, server_round, results, failures):
        assert not failures and len(results) == 5
        assert {p.cid for p, _ in results} == {str(i) for i in range(5)}
        resultados = sorted(results, key=lambda r: int(r[0].cid))
        n = len(self.pesos)
        payloads = [parameters_to_ndarrays(r.parameters) for _, r in resultados]
        assert all(len(p) == n * (2 if self.scaffold else 1) for p in payloads)
        assert all(r.num_examples == len(self.clientes[int(p.cid)].y) for p, r in resultados)
        for cliente in self.clientes:
            recebido = cliente.registros[-1]
            assert recebido["pesos_recebidos_sha256"] == hash_arrays(self.pesos)
            assert recebido["c_recebido_sha256"] == hash_arrays(self.cg)
        self.pesos, self.cg = agregar(self.pesos, self.cg, [p[:n] for p in payloads],
                                     [p[n:] for p in payloads] if self.scaffold else [], 5)
        media_ci = [np.mean(np.stack(cs), axis=0) for cs in zip(*[c.ci for c in self.clientes], strict=True)]
        erro = max(float(np.max(np.abs(a - b))) for a, b in zip(self.cg, media_ci, strict=True))
        assert all(np.allclose(a, b, atol=self.config["atol_controles_float32"],
                               rtol=self.config["rtol_controles_float32"])
                   for a, b in zip(self.cg, media_ci, strict=True))
        path = self.saida / f"rodada-{server_round:02d}.pt"
        salvar_estado(path, server_round, self.pesos, self.cg, [c.ci for c in self.clientes])
        rodada, p, c, cis = ler_estado(path)
        assert rodada == server_round
        assert hash_arrays(p + c + sum(cis, [])) == hash_arrays(
            self.pesos + self.cg + sum([cl.ci for cl in self.clientes], []))
        registros = [cl.registros[-1] for cl in self.clientes]
        assert all(reg["rodada"] == server_round for reg in registros)
        evid = {"rodada": server_round, "participantes": list(range(5)),
                "exemplos": sum(r["exemplos"] for r in registros),
                "passos": sum(r["passos"] for r in registros),
                "pesos_sha256": hash_arrays(self.pesos), "c_sha256": hash_arrays(self.cg),
                "c_norma_l2": float(np.sqrt(sum(np.sum(a.astype(np.float64) ** 2) for a in self.cg))),
                "erro_max_c_media_ci": erro, "persistencia_recarregada_igual_bit_a_bit": True,
                "estado_sha256": sha256(path), "clientes": registros}
        for campo in ("bytes_parametros_recebidos", "bytes_parametros_enviados",
                      "bytes_controles_recebidos", "bytes_controles_enviados"):
            evid[campo] = sum(r[campo] for r in registros)
        self.rodadas.append(evid)
        base.escrever_json(self.saida / "rodadas.json", self.rodadas)
        return ndarrays_to_parameters(self.pesos + (self.cg if self.scaffold else [])), {
            "exemplos_treinados": evid["exemplos"]}


def treinar_metodo(nome, iniciais, x, y, partes, config, saida, contrato, media, escala):
    saida.mkdir()
    inicio = perf_counter()
    scaffold = nome == "scaffold"
    clientes = [ClienteSGD(i, x[idx], y[idx], config, scaffold) for i, idx in enumerate(partes)]
    manager = SimpleClientManager()
    for i, cliente in enumerate(clientes):
        assert manager.register(base.ProxyLocal(str(i), cliente))
    estrategia = Estrategia(iniciais, clientes, config, scaffold, saida)
    server = Server(client_manager=manager, strategy=estrategia)
    server.set_max_workers(1)
    server.fit(num_rounds=config["rodadas"], timeout=None)
    modelo = CNN1D()
    carregar_modelo(modelo, estrategia.pesos)
    checkpoint = {"state_dict": modelo.state_dict(), "media": torch.from_numpy(media),
                  "escala": torch.from_numpy(escala), "contrato": contrato,
                  "metodo": nome, "configuracao_sha256": sha256(saida.parent / "configuracao.json")}
    torch.save(checkpoint, saida / "checkpoint.pt")
    resultado = {"nome": nome, "tempo_treino_s": perf_counter() - inicio,
                 "checkpoint_sha256": sha256(saida / "checkpoint.pt"),
                 "volume": "bytes brutos dos arrays float32 de parametros/controles na simulacao em processo",
                 "mensagem_serializada_medida": False, "rodadas": estrategia.rodadas}
    base.escrever_json(saida / "treino.json", resultado)
    return resultado


def treinar(saida):
    saida.mkdir(parents=True, exist_ok=False)
    inicio = perf_counter()
    config = ler_json(PROTOCOLO)
    protocolo, audit, colunas, x, xv, y, yv, media, escala = validacao.carregar_ajuste_validacao(
        LOCAL / "cicids2017-corrigido", PARTICAO)
    assert config["manifesto_validacao_sha256"] == audit["manifesto_sha256"]
    assert config["fpr_maxima_validacao"] == protocolo["fpr_maxima_validacao"] == 0.01
    assert config["alpha_dirichlet"] == base.ALFA_DIRICHLET
    with patch.object(base.piloto, "CLIENTES", 5):
        partes, tentativa = base.distribuir_dirichlet(y, config["seed_clientes"])
    assert np.array_equal(np.sort(np.concatenate(partes)), np.arange(len(y)))
    torch.manual_seed(config["seed_modelo"])
    iniciais = arrays_modelo(CNN1D())
    anterior = ler_json(LOCAL / "cnn-validacao/execucao/configuracao.json")
    assert hash_arrays(iniciais) == anterior["pesos_iniciais_sha256"]
    contagens = [{"cliente": i, "total": len(idx), "suporte": base.piloto.contar_classes(y[idx]),
                  "indices_no_treino_sha256": validacao.hash_indices(idx)} for i, idx in enumerate(partes)]
    assert contagens == anterior["particoes"]
    ordens = [{"rodada": r, "cliente": i, "seed": config["seed_modelo"] + 100 * r + i,
               "ordem_sha256": hash_arrays([ordem_minibatches(len(idx), config["seed_modelo"] + 100 * r + i)
                                             .numpy().astype("<i8")]),
               "passos": (len(idx) + config["lote"] - 1) // config["lote"]}
              for r in range(1, config["rodadas"] + 1) for i, idx in enumerate(partes)]
    assert ordens == anterior["minibatches"][:len(ordens)]
    contrato = {**anterior["contrato"], "score": "sigmoid do logit DDoS; nao calibrado como probabilidade",
                "embedding": "ReLU da camada linear 48 -> 16", "limiar": 0.5}
    np.savez_compressed(saida / "clientes.npz", **{f"cliente_{i}": a for i, a in enumerate(partes)})
    config.update({"pesos_iniciais_sha256": hash_arrays(iniciais), "particoes": contagens,
                   "minibatches": ordens, "tentativa_particao": tentativa,
                   "exemplos_por_rodada": len(y), "exposicoes_por_metodo": len(y) * config["rodadas"],
                   "passos_por_metodo": sum(o["passos"] for o in ordens),
                   "bytes_por_vetor_de_parametros": sum(a.nbytes for a in iniciais),
                   "contrato": contrato, "auditoria_reutilizada": audit,
                   "normalizacao_media_sha256": hash_arrays([media]),
                   "normalizacao_escala_sha256": hash_arrays([escala]),
                   "clientes_npz_sha256": sha256(saida / "clientes.npz"),
                   "protocolo_scaffold_sha256": sha256(PROTOCOLO),
                   "versoes": {"python": platform.python_version(), "torch": str(torch.__version__),
                                "flower": flwr.__version__, "numpy": np.__version__, "plataforma": platform.platform()},
                   "torch_threads": 2, "torch_interop_threads": 1, "deterministico": True,
                   "diferencas_ensaio_09h04": "SGD lr=0.01, 2 rodadas, media uniforme nos dois metodos; anterior Adam, 3 rodadas, media ponderada por exemplos"})
    base.escrever_json(saida / "configuracao.json", config)
    torch.save([torch.from_numpy(a) for a in iniciais], saida / "pesos_iniciais.pt")
    print("Configuracao fixada antes do treino e da inferencia na validacao.", flush=True)
    treinos = [treinar_metodo(nome, iniciais, x, y, partes, config, saida / nome, contrato, media, escala)
               for nome in config["metodos"]]
    for t in treinos:
        obtidas = [{k: cliente[k] for k in ("rodada", "cliente", "seed", "ordem_sha256", "passos")}
                   for r in t["rodadas"] for cliente in r["clientes"]]
        assert obtidas == ordens
    assert treinos[0]["rodadas"][0]["pesos_sha256"] == treinos[1]["rodadas"][0]["pesos_sha256"]
    base.escrever_json(saida / "pareamento.json", {
        "mesma_inicializacao_particoes_minibatches_orcamento": True,
        "primeira_rodada_pesos_iguais_bit_a_bit": True, "tolerancia_primeira_rodada": 0.0,
        "ci_persistente_entre_rodadas": True, "teste_global_avaliado": False})
    avaliar(saida, dados=(xv, yv, media, escala))
    base.escrever_json(saida / "tempo.json", {"total_s": perf_counter() - inicio})


def avaliar(saida, dados=None):
    config = ler_json(saida / "configuracao.json")
    if dados is None:
        _, _, _, _, xv, _, yv, media, escala = validacao.carregar_ajuste_validacao(
            LOCAL / "cicids2017-corrigido", PARTICAO)
    else:
        xv, yv, media, escala = dados
    resultados = []
    for nome in config["metodos"]:
        caminho = saida / nome
        treino = ler_json(caminho / "treino.json")
        assert sha256(caminho / "checkpoint.pt") == treino["checkpoint_sha256"]
        ck = torch.load(caminho / "checkpoint.pt", map_location="cpu", weights_only=True)
        assert ck["configuracao_sha256"] == sha256(saida / "configuracao.json")
        assert np.array_equal(ck["media"].numpy(), media) and np.array_equal(ck["escala"].numpy(), escala)
        assert ck["contrato"] == config["contrato"]
        modelo = CNN1D()
        modelo.load_state_dict(ck["state_dict"])
        modelo.eval()
        with torch.inference_mode():
            scores = torch.cat([torch.sigmoid(modelo(lote)[0])
                                for lote in torch.from_numpy(xv).split(config["lote"])]).numpy()
        arquivo_scores = caminho / "scores_validacao.npy"
        if arquivo_scores.exists():
            assert np.array_equal(np.load(arquivo_scores, allow_pickle=False), scores)
        else:
            np.save(arquivo_scores, scores, allow_pickle=False)
        resultado = {"nome": nome, "calibrado_validacao": validacao.calibrar(scores, yv, config["fpr_maxima_validacao"]),
                     "limiar_05": validacao.medir_fatia(yv, scores >= 0.5),
                     "scores_sha256": sha256(arquivo_scores)}
        resultados.append(resultado)
    arquivo = saida / "resultados.json"
    resumo = {"teste_global_avaliado": False, "uso": "exploratorio: mesmo conjunto calibra limiar e mede recall",
              "teto_fpr": config["fpr_maxima_validacao"], "resultados": resultados}
    if arquivo.exists():
        assert ler_json(arquivo) == resumo
        print("Recarga dos checkpoints e scores: iguais bit a bit em outro processo.", flush=True)
    else:
        base.escrever_json(arquivo, resumo)
    print(json.dumps(resumo, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=("treinar", "avaliar"))
    parser.add_argument("saida", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    (treinar if args.acao == "treinar" else avaliar)(args.saida)
