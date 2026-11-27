"""Registra o volume de parâmetros no proxy em processo do piloto Flower."""

import argparse
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

import treinar_cnn as base
from flwr.common import parameters_to_ndarrays


def bytes_parametros(modelo):
    return sum(tensor.nbytes for tensor in parameters_to_ndarrays(modelo))


def executar(dados, saida, rodadas):
    registros = defaultdict(list)

    class ProxyMedido(base.ProxyLocal):
        def fit(self, ins, timeout, group_id):
            assert group_id == ins.config["rodada"]
            enviados = bytes_parametros(ins.parameters)
            resposta = super().fit(ins, timeout, group_id)
            registros[group_id].append({
                "cliente": int(self.cid),
                "exemplos": resposta.num_examples,
                "bytes_parametros_enviados": enviados,
                "bytes_parametros_recebidos": bytes_parametros(resposta.parameters),
            })
            return resposta

    with patch.object(base, "ProxyLocal", ProxyMedido):
        base.treinar(dados, saida, rodadas)

    assert sorted(registros) == list(range(1, rodadas + 1))
    resumo = []
    for rodada, registros_cliente in sorted(registros.items()):
        clientes = sorted(registros_cliente, key=lambda r: r["cliente"])
        assert [c["cliente"] for c in clientes] == list(range(base.CLIENTES))
        resumo.append({"rodada": rodada, "participantes": [c["cliente"] for c in clientes],
                       **{k: sum(c[k] for c in clientes) for k in
                          ("exemplos", "bytes_parametros_enviados", "bytes_parametros_recebidos")},
                       "por_cliente": clientes})
    base.escrever_json(saida / "volume_parametros.json", {
        "escopo": "volume de parâmetros da simulação Flower em processo",
        "unidade": "bytes dos elementos dos ndarrays decodificados, medidos em FitIns e FitRes",
        "exclusoes": "cabeçalhos NPY, serialização da mensagem, metadados e sobrecarga de transporte",
        "direcao": "enviados pelo servidor aos clientes; recebidos pelo servidor dos clientes",
        "rodadas": resumo,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dados_corrigidos", type=Path)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--rodadas", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    executar(args.dados_corrigidos, args.saida, args.rodadas)


if __name__ == "__main__":
    main()
