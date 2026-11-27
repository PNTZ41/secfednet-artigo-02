"""Treino CNN-1D em CPU com Flower Server e cinco clientes em processo local."""

import argparse
import hashlib
import json
import os
import platform
import random
from pathlib import Path
from unittest.mock import patch

os.environ["FLWR_TELEMETRY_ENABLED"] = "0"

import flwr
import numpy as np
import torch
from flwr.client import NumPyClient
from flwr.common import DisconnectRes, ndarrays_to_parameters, parameters_to_ndarrays
from flwr.server import Server
from flwr.server.client_manager import SimpleClientManager
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import FedAvg
from torch import nn

import piloto_fedavg as piloto
from avaliar_corrigido import ler_sexta, padronizar, sha256
from avaliar_piloto import ALFA_DIRICHLET, chaves_vetores, distribuir_dirichlet, medir
from cnn1d import CNN1D, DIM_EMBEDDING, FORMATO, NUM_FEATURES, prever


CLIENTES = 5
SEED_MODELO = 23
SEED_PARTICAO = 2305
LOTE = 512
TAXA = 0.001
TREINO_SHA256 = "b1a7e316661ebe6e0d5bb87ec712e989739a9768c38baad2096d91042a9d2247"


def escrever_json(caminho, dados):
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def preparar(pasta):
    arquivo_zip = pasta / "CICIDS2017_improved.zip"
    arquivo_split = pasta / "split_cronologico.npz"
    referencia = json.loads((pasta / "metricas.json").read_bytes())
    hash_zip, hash_split = sha256(arquivo_zip), sha256(arquivo_split)
    assert hash_zip == referencia["zip_sha256"] and hash_split == referencia["split_sha256"]
    dados = ler_sexta(arquivo_zip)
    with np.load(arquivo_split, allow_pickle=False) as manifesto:
        assert manifesto["zip_sha256"].item() == hash_zip
        assert dados.colunas == manifesto["ordem_features"].tolist() and len(dados.colunas) == NUM_FEATURES
        treino, teste = [np.flatnonzero(np.isin(dados.linhas, manifesto[k]))
                         for k in ("linhas_treino", "linhas_teste")]
        assert np.array_equal(dados.linhas[treino], manifesto["linhas_treino"])
        assert np.array_equal(dados.linhas[teste], manifesto["linhas_teste"])
        corte = manifesto["corte_utc_us"].item()
        assert np.array_equal(teste, np.flatnonzero(dados.tempos >= corte))
        assert np.all(dados.tempos[treino] < corte)
    treino, x, xt, ajustes = padronizar(dados, treino, teste)
    hash_treino = hashlib.sha256(dados.linhas[treino].astype("<i8").tobytes()).hexdigest()
    assert hash_treino == referencia["linhas_treino_final_sha256"] == TREINO_SHA256
    assert ajustes == referencia["ajustes_por_vetores_padronizados"]
    y, yt = dados.y[treino], dados.y[teste]
    assert piloto.contar_classes(y) == referencia["treino"]
    assert piloto.contar_classes(yt) == referencia["teste"]
    x, xt = x.astype(np.float32), xt.astype(np.float32)
    assert np.isfinite(x).all() and np.isfinite(xt).all()
    assert not np.intersect1d(chaves_vetores(x), chaves_vetores(xt)).size

    bruto = dados.x[treino]
    media, escala = bruto.mean(axis=0), bruto.std(axis=0)
    escala[escala == 0.0] = 1.0
    assert np.array_equal(((bruto - media) / escala).astype(np.float32), x)
    assert np.array_equal(((dados.x[teste] - media) / escala).astype(np.float32), xt)
    exemplo = teste[np.flatnonzero(yt == 1)[0]]
    amostra = {"features": dados.x[exemplo].tolist(), "registro_csv": int(dados.linhas[exemplo]),
               "rotulo_real": piloto.CLASSES[dados.y[exemplo]]}
    contrato = {
        "formato": FORMATO, "ordem_features": dados.colunas,
        "normalizacao": "(x - média do treino) / desvio do treino (ddof=0; zero vira 1)",
        "dtype_entrada_modelo": "float32", "dtype_normalizacao": "float64",
        "classes": {str(i): nome for i, nome in enumerate(piloto.CLASSES)}, "limiar": piloto.LIMIAR,
        "score": "sigmoide do logit para DDoS, sem calibração",
        "embedding": {"camada": "embedding.1", "ativacao": "ReLU", "dimensao": DIM_EMBEDDING},
        "zip_sha256": hash_zip, "split_sha256": hash_split, "linhas_treino_final_sha256": hash_treino,
        "expurgo_apos_padronizacao": ajustes, "vetores_float32_compartilhados": 0,
    }
    return (x, xt, y, yt, torch.from_numpy(media), torch.from_numpy(escala), amostra, contrato)


def parametros(modelo):
    return [tensor.detach().numpy().copy() for tensor in modelo.state_dict().values()]


def carregar_parametros(modelo, novos):
    modelo.load_state_dict({nome: torch.from_numpy(valor)
                            for nome, valor in zip(modelo.state_dict(), novos, strict=True)})


class ClienteCNN(NumPyClient):
    def __init__(self, numero, x, y):
        self.numero = numero
        self.modelo = CNN1D()
        self.x = torch.from_numpy(x)
        self.y = torch.from_numpy(y.astype(np.float32))

    def get_parameters(self, config):
        return parametros(self.modelo)

    def fit(self, novos_parametros, config):
        carregar_parametros(self.modelo, novos_parametros)
        self.modelo.train()
        otimizador = torch.optim.Adam(self.modelo.parameters(), lr=TAXA)
        bce = nn.BCEWithLogitsLoss()
        seed = SEED_MODELO + 100 * int(config["rodada"]) + self.numero
        gerador = torch.Generator().manual_seed(seed)
        total = len(self.y)
        acumulada = 0.0
        for indices in torch.randperm(total, generator=gerador).split(LOTE):
            otimizador.zero_grad(set_to_none=True)
            logits, _ = self.modelo(self.x[indices])
            perda = bce(logits, self.y[indices])
            if not torch.isfinite(perda):
                raise ArithmeticError(f"Perda não finita no cliente {self.numero}")
            perda.backward()
            otimizador.step()
            acumulada += perda.item() * len(indices)
        return parametros(self.modelo), total, {"perda": acumulada / total}


class ProxyLocal(ClientProxy):
    def __init__(self, cid, cliente):
        super().__init__(cid)
        self.cliente = cliente.to_client()

    def get_properties(self, ins, timeout, group_id):
        return self.cliente.get_properties(ins)

    def get_parameters(self, ins, timeout, group_id):
        return self.cliente.get_parameters(ins)

    def fit(self, ins, timeout, group_id):
        return self.cliente.fit(ins)

    def evaluate(self, ins, timeout, group_id):
        return self.cliente.evaluate(ins)

    def reconnect(self, ins, timeout, group_id):
        return DisconnectRes(reason="simulacao_local")


class FedAvgLocal(FedAvg):
    def aggregate_fit(self, server_round, results, failures):
        if failures:
            raise RuntimeError(f"Flower, rodada {server_round}: {failures!r}")
        if {proxy.cid for proxy, _ in results} != {str(i) for i in range(CLIENTES)}:
            raise RuntimeError(f"Flower recebeu um conjunto incompleto de clientes na rodada {server_round}")
        return super().aggregate_fit(server_round, sorted(results, key=lambda r: r[0].cid), failures)


def agregar_perdas(resultados):
    exemplos = sum(n for n, _ in resultados)
    return {"perda": sum(n * m["perda"] for n, m in resultados) / exemplos,
            "exemplos_treinados": exemplos}


def rodar_flower(modelo, x, y, particoes, rodadas):
    gerenciador = SimpleClientManager()
    for numero, indices in enumerate(particoes):
        cliente = ClienteCNN(numero, x[indices], y[indices])
        assert gerenciador.register(ProxyLocal(str(numero), cliente))
    estrategia = FedAvgLocal(fraction_fit=1.0, fraction_evaluate=0.0, min_fit_clients=CLIENTES,
                            min_available_clients=CLIENTES, min_evaluate_clients=CLIENTES,
                            accept_failures=False, inplace=False,
                            on_fit_config_fn=lambda rodada: {"rodada": rodada},
                            fit_metrics_aggregation_fn=agregar_perdas,
                            initial_parameters=ndarrays_to_parameters(parametros(modelo)))
    servidor = Server(client_manager=gerenciador, strategy=estrategia)
    servidor.set_max_workers(1)
    historico, _ = servidor.fit(num_rounds=rodadas, timeout=None)
    assert historico.metrics_distributed_fit["exemplos_treinados"] == [
        (rodada, len(y)) for rodada in range(1, rodadas + 1)]
    carregar_parametros(modelo, parameters_to_ndarrays(servidor.parameters))
    return historico.metrics_distributed_fit


@torch.inference_mode()
def medir_no_teste(modelo, xt, yt):
    modelo.eval()
    lotes = torch.from_numpy(xt).split(LOTE)
    previsto = torch.cat([torch.sigmoid(modelo(lote)[0]) >= piloto.LIMIAR for lote in lotes]).numpy()
    resultado = medir(yt, previsto)
    resultado["fpr"] = resultado["falsos_positivos_ddos"] / int(np.count_nonzero(yt == 0))
    return resultado


def treinar(pasta, saida, rodadas):
    saida.mkdir(parents=True, exist_ok=False)
    random.seed(SEED_MODELO)
    torch.manual_seed(SEED_MODELO)
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    x, xt, y, yt, media, escala, amostra, contrato = preparar(pasta)
    with patch.object(piloto, "CLIENTES", CLIENTES):
        particoes, tentativa = distribuir_dirichlet(y, SEED_PARTICAO)
    assert np.array_equal(np.sort(np.concatenate(particoes)), np.arange(len(y)))
    config = {"clientes": CLIENTES, "alpha_dirichlet": ALFA_DIRICHLET, "seed_particao": SEED_PARTICAO,
              "tentativa_aceita": tentativa, "seed_modelo": SEED_MODELO, "rodadas": rodadas,
              "epocas_locais": 1, "lote": LOTE, "otimizador": "Adam", "taxa": TAXA,
              "dispositivo": "cpu", "torch_threads": 2, "validacao_para_ajuste": False,
              "python": platform.python_version(), "pytorch": str(torch.__version__),
              "flower": str(flwr.__version__), "numpy": np.__version__}
    auditoria = {"configuracao": config, "treino": piloto.contar_classes(y), "teste": piloto.contar_classes(yt),
                 "treino_atribuido_exatamente_uma_vez": True,
                 "contagens_clientes": [{"cliente": i, "total": len(idx), **piloto.contar_classes(y[idx])}
                                       for i, idx in enumerate(particoes)]}
    escrever_json(saida / "contrato.json", contrato)
    escrever_json(saida / "particao.json", auditoria)
    print("Pré-processamento e partição auditados.", flush=True)

    modelo = CNN1D()
    historico = rodar_flower(modelo, x, y, particoes, rodadas)
    metricas = medir_no_teste(modelo, xt, yt)
    checkpoint = saida / "checkpoint_cnn1d.pt"
    torch.save({"state_dict": modelo.state_dict(), "contrato": contrato,
                "media": media, "escala": escala}, checkpoint)
    escrever_json(saida / "exemplo_entrada.json", amostra)
    resultado = {"preliminar": True, "treino": auditoria["treino"], "teste": auditoria["teste"],
                 "historico_flower": historico, "metricas": metricas, "checkpoint_sha256": sha256(checkpoint),
                 "parametros_do_modelo": sum(p.numel() for p in modelo.parameters()),
                 "exemplo_em_memoria": prever(modelo, contrato, media, escala, amostra["features"])}
    escrever_json(saida / "metricas.json", resultado)
    print(json.dumps(metricas, ensure_ascii=False, indent=2, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dados_corrigidos", type=Path)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--rodadas", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    treinar(args.dados_corrigidos, args.saida, args.rodadas)


if __name__ == "__main__":
    main()
