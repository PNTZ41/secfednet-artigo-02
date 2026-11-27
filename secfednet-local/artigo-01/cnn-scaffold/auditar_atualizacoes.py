"""Validação no servidor antes da agregação FedAvg-SGD."""

import math

import numpy as np


def agregar_auditado(globais, controles, atualizacoes, clientes_esperados, agregador):
    """Valida todos os deltas antes de chamar a mesma agregação do controle."""
    if set(atualizacoes) != set(clientes_esperados):
        raise ValueError("Participantes recebidos diferem dos esperados")
    deltas = []
    auditoria = []
    for cliente in sorted(clientes_esperados):
        delta = atualizacoes[cliente]
        if len(delta) != len(globais):
            raise ValueError(f"Cliente {cliente}: quantidade de tensores incompatível")
        quadrados = []
        for i, (tensor, referencia) in enumerate(zip(delta, globais, strict=True)):
            if tensor.shape != referencia.shape or tensor.dtype != referencia.dtype:
                raise ValueError(f"Cliente {cliente}, tensor {i}: dimensões ou dtype incompatíveis")
            if not np.isfinite(tensor).all():
                raise ValueError(f"Cliente {cliente}, tensor {i}: valor não finito")
            quadrados.append(float(np.sum(np.square(tensor.astype(np.float64)))))
        auditoria.append({"cliente": cliente, "norma_l2_delta_pesos": math.sqrt(math.fsum(quadrados))})
        deltas.append(delta)
    pesos, controles_novos = agregador(globais, controles, deltas, [], len(clientes_esperados))
    if not all(np.isfinite(tensor).all() for tensor in pesos):
        raise ValueError("Pesos agregados não finitos")
    return pesos, controles_novos, auditoria
