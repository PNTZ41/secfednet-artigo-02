"""Oráculo escalar de duas rodadas e retomada em outro processo."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

from scaffold import agregar, hash_arrays, ler_estado, local_sgd, salvar_estado, zeros


def rodada(pesos, cg, locais):
    deltas, novos_locais, deltas_c = [], [], []
    for cid, alvo in enumerate((1.0, 3.0)):
        modelo = torch.nn.Linear(1, 1, bias=False, dtype=torch.float64)
        delta, ci, dc, evidencia = local_sgd(
            modelo, torch.ones((1, 1), dtype=torch.float64), torch.tensor([alvo], dtype=torch.float64),
            pesos, cg, locais[cid], scaffold=True, seed=23, lote=1, lr=0.1,
            perda_fn=lambda pred, real: 0.5 * torch.mean((pred - real) ** 2))
        assert evidencia["passos"] == 1
        deltas.append(delta)
        novos_locais.append(ci)
        deltas_c.append(dc)
    pesos, cg = agregar(pesos, cg, deltas, deltas_c, total_clientes=2)
    return pesos, cg, novos_locais


def valores(pesos, cg, locais):
    return {"w": pesos[0].item(), "c": cg[0].item(), "ci": [c[0].item() for c in locais]}


def testar(saida):
    saida.mkdir(parents=True, exist_ok=False)
    p = [np.array([[0.0]], dtype=np.float64)]
    cg, locais = zeros(p), [zeros(p), zeros(p)]
    r1 = rodada(p, cg, locais)
    # f_i(w)=(w-a_i)^2/2, a=(1,3), eta=0.1, K=1.
    for observado, esperado in zip([r1[0][0].item(), r1[1][0].item(), *[c[0].item() for c in r1[2]]],
                                   [0.2, -2.0, -1.0, -3.0], strict=True):
        assert abs(observado - esperado) <= 1e-12
    salvar_estado(saida / "rodada-01.pt", 1, *r1)
    r2 = rodada(*r1)
    for observado, esperado in zip([r2[0][0].item(), r2[1][0].item(), *[c[0].item() for c in r2[2]]],
                                   [0.38, -1.8, -0.8, -2.8], strict=True):
        assert abs(observado - esperado) <= 1e-12
    salvar_estado(saida / "continuo-02.pt", 2, *r2)
    subprocess.run([sys.executable, "-B", __file__, "retomar", str(saida / "rodada-01.pt"),
                    str(saida / "retomado-02.pt")], check=True)
    n, pr, cr, lir = ler_estado(saida / "retomado-02.pt")
    assert n == 2
    assert hash_arrays(pr + cr + sum(lir, [])) == hash_arrays(r2[0] + r2[1] + sum(r2[2], []))
    # Controle local não pode ser zerado na segunda rodada.
    resetado = rodada(r1[0], r1[1], [zeros(p), zeros(p)])
    assert abs(resetado[0][0].item() - r2[0][0].item()) > 1e-3
    # Na participação parcial, c usa N total, não o número de participantes.
    _, parcial = agregar(p, cg, [[np.array([[0.1]])]], [[np.array([[1.0]])]], total_clientes=5)
    assert abs(parcial[0].item() - 0.2) <= 1e-12
    resultado = {"rodada_1": valores(*r1), "rodada_2": valores(*r2),
                 "tolerancia_absoluta": 1e-12, "retomada_outro_processo_igual_bit_a_bit": True,
                 "resetar_ci_e_detectado": True, "divisor_N_participacao_parcial_verificado": True,
                 "torch_load_weights_only": True}
    (saida / "resultado.json").write_text(json.dumps(resultado, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resultado, indent=2))


if __name__ == "__main__":
    torch.set_num_threads(1)
    if sys.argv[1] == "retomar":
        n, p, cg, locais = ler_estado(Path(sys.argv[2]))
        assert n == 1
        salvar_estado(Path(sys.argv[3]), 2, *rodada(p, cg, locais))
    else:
        assert sys.argv[1] == "testar"
        testar(Path(sys.argv[2]))
