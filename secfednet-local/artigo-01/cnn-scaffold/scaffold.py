"""SCAFFOLD, opção II: SGD, controles persistentes e média uniforme.

Algoritmo 1: https://proceedings.mlr.press/v119/karimireddy20a.html
Sem momentum, weight decay ou taxa variável. K é o número real de minibatches.
"""

import hashlib

import numpy as np
import torch


def hash_arrays(arrays):
    return hashlib.sha256(b"".join(a.tobytes() for a in arrays)).hexdigest()


def arrays_modelo(modelo):
    # Esta implementação admite apenas modelos sem buffers não treináveis.
    assert list(modelo.state_dict()) == [n for n, _ in modelo.named_parameters()]
    return [p.detach().cpu().numpy().copy() for p in modelo.parameters()]


def carregar_modelo(modelo, arrays):
    modelo.load_state_dict({k: torch.from_numpy(a.copy()) for k, a in
                            zip(modelo.state_dict(), arrays, strict=True)})


def zeros(arrays):
    return [np.zeros_like(a) for a in arrays]


def ordem_minibatches(total, seed):
    return torch.randperm(total, generator=torch.Generator().manual_seed(seed))


def local_sgd(modelo, x, y, globais, c_global, c_local, *, scaffold, seed, lote, lr, perda_fn):
    """Retorna Δpesos, novo c_i, Δc_i e evidência do orçamento efetivo."""
    assert len(y) > 0 and lr > 0 and lote > 0
    carregar_modelo(modelo, globais)
    modelo.train()
    referencia = [torch.from_numpy(a.copy()) for a in globais]
    cg = [torch.from_numpy(a.copy()) for a in c_global]
    ci = [torch.from_numpy(a.copy()) for a in c_local]
    otimizador = torch.optim.SGD(modelo.parameters(), lr=lr, momentum=0, weight_decay=0)
    ordem = ordem_minibatches(len(y), seed)
    passos, acumulada = 0, 0.0
    for idx in ordem.split(lote):
        otimizador.zero_grad(set_to_none=True)
        saida = modelo(x[idx])
        logits = saida[0] if isinstance(saida, tuple) else saida.reshape(-1)
        perda = perda_fn(logits, y[idx])
        assert torch.isfinite(perda)
        perda.backward()
        if scaffold:
            with torch.no_grad():
                for p, g, i in zip(modelo.parameters(), cg, ci, strict=True):
                    assert p.grad is not None
                    p.grad.add_(g - i)
        otimizador.step()
        acumulada += perda.item() * len(idx)
        passos += 1
    finais = arrays_modelo(modelo)
    assert all(np.isfinite(a).all() for a in finais)
    if scaffold:
        with torch.no_grad():
            novos_c = [(i - g + (w - p.detach()) / (passos * lr)).numpy().copy()
                       for i, g, w, p in zip(ci, cg, referencia, modelo.parameters(), strict=True)]
        delta_c = [novo - antigo for novo, antigo in zip(novos_c, c_local, strict=True)]
    else:
        novos_c, delta_c = [a.copy() for a in c_local], []
    assert all(np.isfinite(a).all() for a in novos_c)
    return ([a - b for a, b in zip(finais, globais, strict=True)], novos_c, delta_c,
            {"passos": passos, "exemplos": len(y), "seed": seed,
             "ordem_sha256": hash_arrays([ordem.numpy().astype("<i8")]),
             "perda": acumulada / len(y)})


def agregar(globais, c_global, deltas_pesos, deltas_controles, total_clientes):
    assert deltas_pesos and len(deltas_pesos) <= total_clientes
    novos = [w + np.mean(np.stack(ds), axis=0)
             for w, ds in zip(globais, zip(*deltas_pesos, strict=True), strict=True)]
    if deltas_controles:
        cg = [c + np.sum(np.stack(ds), axis=0) / total_clientes
              for c, ds in zip(c_global, zip(*deltas_controles, strict=True), strict=True)]
    else:
        cg = [a.copy() for a in c_global]
    return novos, cg


def salvar_estado(caminho, rodada, pesos, c_global, c_locais):
    tensorizar = lambda arrays: [torch.from_numpy(a.copy()) for a in arrays]
    torch.save({"rodada": rodada, "pesos": tensorizar(pesos),
                "c_global": tensorizar(c_global),
                "c_locais": [tensorizar(c) for c in c_locais]}, caminho)


def ler_estado(caminho):
    estado = torch.load(caminho, map_location="cpu", weights_only=True)
    arrays = lambda ts: [t.numpy().copy() for t in ts]
    return (estado["rodada"], arrays(estado["pesos"]), arrays(estado["c_global"]),
            [arrays(c) for c in estado["c_locais"]])
