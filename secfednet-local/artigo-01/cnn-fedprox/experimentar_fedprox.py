"""Compara FedAvg e FedProx na CNN e nas partições congeladas do Artigo 01."""

import argparse
import hashlib
import json
import random
from collections import defaultdict
from functools import partial
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np
import torch
from flwr.server.strategy import FedProx
from torch import nn

import treinar_cnn as base
from avaliar_clientes import medir_fatia
from avaliar_corrigido import ler_sexta, sha256
from cnn1d import CNN1D
from treinar_instrumentado import bytes_parametros


ATOL = 1e-7
RTOL = 1e-6
RODADAS = 3
ENSAIOS = (("fedavg", None), ("fedprox_mu0", 0.0), ("fedprox_mu001", 0.01))


def hash_array(valores):
    return hashlib.sha256(np.asarray(valores).tobytes()).hexdigest()


def hash_pesos(modelo):
    return hashlib.sha256(b"".join(p.tobytes() for p in base.parametros(modelo))).hexdigest()


def penalizacao(parametros, referencia, mu):
    soma = sum((local - global_fixo).square().sum()
               for local, global_fixo in zip(parametros, referencia, strict=True))
    return (mu / 2) * soma


def conferir_penalizacao():
    a = nn.Parameter(torch.tensor([2.0, 4.0], dtype=torch.float64))
    b = nn.Parameter(torch.tensor([-1.0], dtype=torch.float64))
    referencia = (torch.tensor([1.0, 2.0], dtype=torch.float64),
                  torch.tensor([1.0], dtype=torch.float64))
    perda = penalizacao((a, b), referencia, 0.2)
    # (0.2 / 2) * ((2 - 1)^2 + (4 - 2)^2 + (-1 - 1)^2) = 0.9.
    torch.testing.assert_close(perda, torch.tensor(0.9, dtype=torch.float64), atol=1e-15, rtol=0)
    perda.backward()
    torch.testing.assert_close(a.grad, torch.tensor([0.2, 0.4], dtype=torch.float64))
    torch.testing.assert_close(b.grad, torch.tensor([-0.4], dtype=torch.float64))
    assert all(not p.requires_grad and p.grad is None for p in referencia)
    with torch.no_grad():
        a.add_(1)
    assert torch.equal(referencia[0], torch.tensor([1.0, 2.0], dtype=torch.float64))
    torch.testing.assert_close(penalizacao((a, b), referencia, 0), torch.tensor(0.0, dtype=torch.float64))
    return {"mu": 0.2, "soma_quadratica_manual": 9, "penalizacao_esperada": 0.9,
            "penalizacao_observada": perda.item(), "gradientes_conferidos": True}


class ClienteProx(base.ClienteCNN):
    def fit(self, novos_parametros, config):
        base.carregar_parametros(self.modelo, novos_parametros)
        globais = tuple(p.detach().clone() for p in self.modelo.parameters())
        self.modelo.train()
        otimizador = torch.optim.Adam(self.modelo.parameters(), lr=base.TAXA)
        bce = nn.BCEWithLogitsLoss()
        mu = float(config["proximal_mu"])
        gerador = torch.Generator().manual_seed(base.SEED_MODELO + 100 * int(config["rodada"]) + self.numero)
        acumulada = 0.0
        for indices in torch.randperm(len(self.y), generator=gerador).split(base.LOTE):
            otimizador.zero_grad(set_to_none=True)
            logits, _ = self.modelo(self.x[indices])
            perda = bce(logits, self.y[indices]) + penalizacao(self.modelo.parameters(), globais, mu)
            if not torch.isfinite(perda):
                raise ArithmeticError(f"Perda não finita no cliente {self.numero}")
            perda.backward()
            otimizador.step()
            acumulada += perda.item() * len(indices)
        # O snapshot permanece fixo e sem grafo durante todos os minibatches locais.
        for global_fixo, recebido in zip(globais, novos_parametros, strict=True):
            assert not global_fixo.requires_grad and global_fixo.grad is None
            assert np.array_equal(global_fixo.numpy(), recebido)
        return base.parametros(self.modelo), len(self.y), {"perda": acumulada / len(self.y)}


class EstrategiaProx(base.FedAvgLocal, FedProx):
    def __init__(self, *, proximal_mu, inplace=False, **kwargs):
        super().__init__(proximal_mu=proximal_mu, **kwargs)
        self.inplace = inplace


def configuracao(particoes, y, contrato, modelo, tentativa):
    ordens = []
    for rodada in range(1, RODADAS + 1):
        for cliente, idx in enumerate(particoes):
            seed = base.SEED_MODELO + 100 * rodada + cliente
            ordem = torch.randperm(len(idx), generator=torch.Generator().manual_seed(seed))
            ordens.append({"rodada": rodada, "cliente": cliente, "seed": seed,
                           "ordem_sha256": hash_array(ordem.numpy().astype("<i8")),
                           "passos": (len(idx) + base.LOTE - 1) // base.LOTE})
    return {
        "ensaios": [{"nome": nome, "mu": mu} for nome, mu in ENSAIOS],
        "rodadas": RODADAS, "epocas_locais": 1, "clientes": base.CLIENTES,
        "seed_modelo": base.SEED_MODELO, "seed_particao": base.SEED_PARTICAO,
        "alpha_dirichlet": base.ALFA_DIRICHLET, "tentativa_particao": tentativa,
        "pesos_iniciais_sha256": hash_pesos(modelo), "minibatches": ordens,
        "particoes": [{"cliente": i, "total": len(idx), "suporte": base.piloto.contar_classes(y[idx]),
                       "indices_no_treino_sha256": hash_array(idx.astype("<i8"))}
                      for i, idx in enumerate(particoes)],
        "otimizador": "Adam reinicializado por cliente e rodada", "lr": base.TAXA,
        "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0, "lote": base.LOTE,
        "exemplos_por_rodada": len(y), "exposicoes_por_metodo": RODADAS * len(y),
        "passos_otimizador_por_metodo": sum(e["passos"] for e in ordens),
        "torch_threads": 2, "torch_interop_threads": 1, "dispositivo": "cpu",
        "limiar": contrato["limiar"], "contrato": contrato,
        "tolerancia_mu0": {"atol_pesos": ATOL, "rtol_pesos": RTOL, "atol_metricas": ATOL},
        "selecao_mu": "0.01 exploratório, fixado antes dos treinos e da avaliação; sem ajuste no teste",
        "versoes": {"python": base.platform.python_version(), "torch": str(torch.__version__),
                    "flower": base.flwr.__version__, "numpy": np.__version__},
    }


def treinar_metodo(nome, mu, inicial, x, y, particoes, config, saida, media, escala):
    random.seed(base.SEED_MODELO)
    torch.manual_seed(base.SEED_MODELO)
    modelo = CNN1D()
    modelo.load_state_dict(inicial)
    assert hash_pesos(modelo) == config["pesos_iniciais_sha256"]
    eventos = defaultdict(list)
    esperadas = {(e["rodada"], e["cliente"]): e for e in config["minibatches"]}
    randperm_original = torch.randperm

    class ProxyMedido(base.ProxyLocal):
        def fit(self, ins, timeout, group_id):
            cliente, rodada = int(self.cid), int(ins.config["rodada"])
            assert group_id == rodada
            enviados = bytes_parametros(ins.parameters)
            ordens = []

            def registrar_ordem(*args, **kwargs):
                indices = randperm_original(*args, **kwargs)
                ordens.append(hash_array(indices.numpy().astype("<i8")))
                return indices

            inicio = perf_counter()
            with patch.object(torch, "randperm", registrar_ordem):
                resposta = super().fit(ins, timeout, group_id)
            duracao = perf_counter() - inicio
            assert ordens == [esperadas[rodada, cliente]["ordem_sha256"]]
            assert resposta.num_examples == len(particoes[cliente])
            eventos[rodada].append({"cliente": cliente, "exemplos": resposta.num_examples,
                                    "enviados_bytes": enviados,
                                    "recebidos_bytes": bytes_parametros(resposta.parameters),
                                    "tempo_fit_s": duracao, "ordem_sha256": ordens[0]})
            return resposta

    inicio = perf_counter()
    with patch.object(base, "ProxyLocal", ProxyMedido):
        if mu is None:
            historico = base.rodar_flower(modelo, x, y, particoes, RODADAS)
        else:
            with patch.object(base, "ClienteCNN", ClienteProx), patch.object(
                    base, "FedAvgLocal", partial(EstrategiaProx, proximal_mu=mu)):
                historico = base.rodar_flower(modelo, x, y, particoes, RODADAS)
    duracao = perf_counter() - inicio
    volume = []
    for rodada in range(1, RODADAS + 1):
        clientes = sorted(eventos[rodada], key=lambda c: c["cliente"])
        assert [c["cliente"] for c in clientes] == list(range(base.CLIENTES))
        volume.append({"rodada": rodada, "clientes": clientes,
                       **{k: sum(c[k] for c in clientes) for k in
                          ("exemplos", "enviados_bytes", "recebidos_bytes", "tempo_fit_s")}})
    pasta = saida / nome
    pasta.mkdir()
    checkpoint = pasta / "checkpoint.pt"
    torch.save({"state_dict": modelo.state_dict(), "contrato": config["contrato"],
                "media": media, "escala": escala}, checkpoint)
    return {"mu": mu, "tempo_flower_s": duracao, "historico": historico, "rodadas": volume,
            "checkpoint_sha256": sha256(checkpoint), "pesos_finais_sha256": hash_pesos(modelo)}


def carregar_fatias(dados, manifesto_path, contrato):
    with np.load(dados / "split_cronologico.npz", allow_pickle=False) as global_split:
        linhas = global_split["linhas_teste"]
    with np.load(manifesto_path, allow_pickle=False) as fatias:
        assert fatias["split_global_sha256"].item() == contrato["split_sha256"]
        assert fatias["treino_final_sha256"].item() == contrato["linhas_treino_final_sha256"]
        assert fatias["linhas_teste_global_sha256"].item() == hash_array(linhas.astype("<i8"))
        indices = []
        for i in range(base.CLIENTES):
            originais = fatias[f"cliente_{i}"]
            idx = np.searchsorted(linhas, originais)
            assert np.array_equal(linhas[idx], originais)
            indices.append(idx)
    assert np.array_equal(np.sort(np.concatenate(indices)), np.arange(len(linhas)))
    return indices


def avaliar_checkpoint(caminho, hash_esperado, xt, yt, fatias, contrato):
    assert sha256(caminho) == hash_esperado
    checkpoint = torch.load(caminho, map_location="cpu", weights_only=True)
    assert checkpoint["contrato"] == contrato
    modelo = CNN1D()
    modelo.load_state_dict(checkpoint["state_dict"])
    modelo.eval()
    with torch.inference_mode():
        previsto = torch.cat([torch.sigmoid(modelo(lote)[0]) >= contrato["limiar"]
                              for lote in torch.from_numpy(xt).split(base.LOTE)]).numpy()
    clientes = [{"cliente": i, **medir_fatia(yt[idx], previsto[idx])} for i, idx in enumerate(fatias)]
    global_ = medir_fatia(yt, previsto)
    assert np.array_equal(np.sum([c["matriz_real_por_previsto"] for c in clientes], axis=0),
                          global_["matriz_real_por_previsto"])
    return {"clientes": clientes, "global": global_}, checkpoint["state_dict"]


def executar(dados, piloto, manifesto, saida):
    inicio_total = perf_counter()
    saida.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    teste_manual = conferir_penalizacao()
    base.escrever_json(saida / "teste_penalizacao.json", teste_manual)
    x, xt, y, yt, media, escala, _, contrato = base.preparar(dados)
    with patch.object(base.piloto, "CLIENTES", base.CLIENTES):
        particoes, tentativa = base.distribuir_dirichlet(y, base.SEED_PARTICAO)
    assert np.array_equal(np.sort(np.concatenate(particoes)), np.arange(len(y)))
    referencia = json.loads((piloto / "artefatos/particao.json").read_bytes())
    assert [{"cliente": i, "total": len(idx), **base.piloto.contar_classes(y[idx])}
            for i, idx in enumerate(particoes)] == referencia["contagens_clientes"]
    torch.manual_seed(base.SEED_MODELO)
    modelo = CNN1D()
    inicial = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
    config = configuracao(particoes, y, contrato, modelo, tentativa)
    config["manifesto_fatias_sha256"] = sha256(manifesto)
    fatias = carregar_fatias(dados, manifesto, contrato)
    base.escrever_json(saida / "configuracao.json", config)
    torch.save(inicial, saida / "pesos_iniciais.pt")
    print("Configuração e penalização verificadas. Iniciando os três treinos sem avaliar o teste.", flush=True)
    treinados = {}
    for nome, mu in ENSAIOS:
        treinados[nome] = treinar_metodo(nome, mu, inicial, x, y, particoes, config, saida, media, escala)
        base.escrever_json(saida / nome / "treino.json", treinados[nome])
        print(f"{nome}: treino encerrado em {treinados[nome]['tempo_flower_s']:.3f} s.", flush=True)

    resultados, estados = {}, {}
    for nome, _ in ENSAIOS:
        inicio = perf_counter()
        resultado, estado = avaliar_checkpoint(saida / nome / "checkpoint.pt",
                                              treinados[nome]["checkpoint_sha256"], xt, yt, fatias, contrato)
        resultado["tempo_avaliacao_s"] = perf_counter() - inicio
        resultados[nome], estados[nome] = resultado, estado
        base.escrever_json(saida / nome / "avaliacao.json", resultado)
    max_diff = max(float((estados["fedavg"][k] - estados["fedprox_mu0"][k]).abs().max())
                   for k in inicial)
    for chave in inicial:
        torch.testing.assert_close(estados["fedavg"][chave], estados["fedprox_mu0"][chave], atol=ATOL, rtol=RTOL)
    comparacao = {"diferenca_maxima_pesos_mu0": max_diff,
                  "pesos_mu0_dentro_da_tolerancia": True,
                  "metricas_mu0_identicas": resultados["fedavg"]["clientes"] == resultados["fedprox_mu0"]["clientes"]
                  and resultados["fedavg"]["global"] == resultados["fedprox_mu0"]["global"]}
    assert comparacao["metricas_mu0_identicas"]
    original = torch.load(piloto / "artefatos/checkpoint_cnn1d.pt", map_location="cpu", weights_only=True)
    comparacao["fedavg_pesos_iguais_ao_piloto"] = all(torch.equal(original["state_dict"][k], estados["fedavg"][k])
                                                            for k in inicial)
    assert comparacao["fedavg_pesos_iguais_ao_piloto"]
    tempo_total = perf_counter() - inicio_total
    base.escrever_json(saida / "comparacao.json", {**comparacao, "tempo_total_s": tempo_total})
    print(json.dumps({"comparacao": comparacao, "globais": {k: v["global"] for k, v in resultados.items()}}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dados_corrigidos", type=Path)
    parser.add_argument("piloto", type=Path)
    parser.add_argument("manifesto_fatias", type=Path)
    parser.add_argument("saida", type=Path)
    args = parser.parse_args()
    executar(args.dados_corrigidos, args.piloto, args.manifesto_fatias, args.saida)


if __name__ == "__main__":
    main()
