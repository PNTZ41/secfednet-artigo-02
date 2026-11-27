"""Executa uma rodada limpa com os clientes locais e a agregação auditada."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from auditar_atualizacoes import agregar_auditado


LOCAL = Path(__file__).resolve().parents[1]
REFERENCIA = LOCAL / "cnn-scaffold/ensaio-20-rodadas/execucao"
PARTICAO = LOCAL / "cnn-validacao/particao/manifesto_validacao.npz"
DIGESTS_VM = {
    "rodada-09.pt": "2bd04013797041c291013ac82c32ad2e25ce3e8110b5d80f24cf97bf1ffdd062",
    "checkpoint.pt": "4e73b24cf7042eace103969787d86f07084ddc4eb558a01fe3bcf32562898922",
    "rodada-10.pt": "8be0ec6a061c77d5c3e806d4c6ca8b3983b514ab89cff374011d392e914808da",
    "scores_validacao_10.npy": "56506368572736c705ac4f94bb4b9c6c4a905fbcea72d858387ceddeb550e198",
}


def exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def sha256(path):
    with path.open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def conferir_sha256(path, esperado):
    exigir(sha256(path) == esperado, f"SHA-256 divergente: {path}")


def ler_particoes(dados, config, colunas, media, escala):
    """Aceita somente exportação dos subconjuntos internos congelados."""
    exigir(sha256(PARTICAO) == config["manifesto_validacao_sha256"], "Manifesto interno divergente")
    clientes = REFERENCIA / "clientes.npz"
    conferir_sha256(clientes, config["clientes_npz_sha256"])
    resultados = []
    with np.load(PARTICAO, allow_pickle=False) as m, np.load(dados, allow_pickle=False) as z:
        exigir(m["ordem_features"].tolist() == colunas == z["ordem_features"].tolist(),
               "Ordem dos atributos divergente")
        for nome, suporte in (("ajuste", (163096, 40155)), ("validacao", (40776, 10039))):
            ids, x, y = (z[f"{campo}_{nome}"] for campo in ("ids", "x", "y"))
            exigir(np.array_equal(ids, m[nome]), f"IDs fora da partição congelada: {nome}")
            exigir(x.shape == (ids.size, 81) and x.dtype == np.dtype("float64") and np.isfinite(x).all(),
                   f"Esperados 81 atributos brutos float64 finitos: {nome}")
            exigir(y.shape == (ids.size,) and np.isin(y, [0, 1]).all() and
                   tuple(np.count_nonzero(y == i) for i in (0, 1)) == suporte,
                   f"Suporte ou rótulos divergentes: {nome}")
            if nome == "ajuste":
                x = np.ascontiguousarray(x)
                desvio = x.std(axis=0)
                desvio[desvio == 0] = 1
                exigir(np.array_equal(x.mean(axis=0), media) and np.array_equal(desvio, escala),
                       "Estatísticas do ajuste divergem do checkpoint")
            normalizado = ((x - media) / escala).astype(np.float32)
            exigir(np.isfinite(normalizado).all(), f"Normalização não finita: {nome}")
            resultados.extend((normalizado, y))
    with np.load(clientes, allow_pickle=False) as z:
        partes = [z[f"cliente_{i}"] for i in range(5)]
    exigir(np.array_equal(np.sort(np.concatenate(partes)), np.arange(len(resultados[1]))),
           "Partição dos clientes não cobre o ajuste exatamente uma vez")
    return (*resultados, partes)


def retomar(artefatos, dados, saida):
    faltam = [str(artefatos / nome) for nome in DIGESTS_VM if not (artefatos / nome).is_file()]
    if not dados.is_file():
        faltam.append(str(dados))
    if faltam:
        raise SystemExit("Insumos ausentes:\n" + "\n".join(faltam))
    exigir(not saida.exists(), f"Destino já existe: {saida}")
    for nome, esperado in DIGESTS_VM.items():
        conferir_sha256(artefatos / nome, esperado)

    import torch

    from experimentar_20 import inferir
    from experimentar_scaffold import ClienteSGD
    from scaffold import agregar, carregar_modelo, hash_arrays, ler_estado, salvar_estado

    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    config = json.loads((REFERENCIA / "configuracao.json").read_text())
    historico = json.loads((REFERENCIA / "fedavg_sgd/rodadas.json").read_text())
    estado, globais, controles, locais = ler_estado(artefatos / "rodada-09.pt")
    rodada = estado + 1
    exigir(rodada == 10 and historico[8]["rodada"] == 9 and
           hash_arrays(globais) == historico[8]["pesos_sha256"], "Estado da rodada 9 divergente")
    exigir(len(locais) == 5 and all(not np.any(a) for a in controles) and
           all(not np.any(a) for ci in locais for a in ci), "FedAvg limpo deve ter controles zerados")
    checkpoint = torch.load(artefatos / "checkpoint.pt", map_location="cpu", weights_only=True)
    exigir(checkpoint["metodo"] == "fedavg_sgd" and checkpoint["contrato"] == config["contrato"],
           "Checkpoint de referência incompatível")
    media, escala = (checkpoint[k].detach().numpy() for k in ("media", "escala"))
    for k, v in (("media", media), ("escala", escala)):
        exigir(v.shape == (81,) and v.dtype == np.dtype("float64") and np.isfinite(v).all() and
               hash_arrays([v]) == config[f"normalizacao_{k}_sha256"], f"Normalizador divergente: {k}")
    exigir(np.all(escala > 0), "Escala precisa ser positiva")
    colunas = checkpoint["contrato"]["ordem_features"]
    x, y, xv, yv, partes = ler_particoes(dados, config, colunas, media, escala)
    torch.manual_seed(config["seed_modelo"])
    clientes = [ClienteSGD(i, x[idx], y[idx], config, False) for i, idx in enumerate(partes)]
    esperados = {r["cliente"]: r for r in config["minibatches"] if r["rodada"] == rodada}
    recebidos = {}
    for i, cliente in enumerate(clientes):
        delta, n, _ = cliente.fit(globais, {"rodada": rodada})
        registro = cliente.registros[-1]
        exigir(n == len(partes[i]) and all(registro[k] == esperados[i][k]
                                           for k in ("rodada", "cliente", "seed", "ordem_sha256", "passos")),
               f"Cliente {i}: execução fora do protocolo de lote")
        recebidos[i] = delta
    pesos, controles, normas = agregar_auditado(globais, controles, recebidos, range(5), agregar)
    modelo = clientes[0].modelo
    carregar_modelo(modelo, pesos)
    scores, _ = inferir(modelo, xv, yv, config["lote"])
    _, pesos_ref, _, _ = ler_estado(artefatos / "rodada-10.pt")
    scores_ref = np.load(artefatos / "scores_validacao_10.npy", allow_pickle=False)
    pesos_iguais = hash_arrays(pesos) == hash_arrays(pesos_ref)
    scores_iguais = hash_arrays([scores]) == hash_arrays([scores_ref]) and scores.shape == scores_ref.shape
    saida.mkdir(parents=True, exist_ok=False)
    salvar_estado(saida / "rodada-10.pt", rodada, pesos, controles, [c.ci for c in clientes])
    np.save(saida / "scores_validacao_10.npy", scores, allow_pickle=False)
    resultado = {"rodada": rodada, "pesos_bit_a_bit": pesos_iguais, "scores_bit_a_bit": scores_iguais,
                 "dados_internos_sha256": sha256(dados), "entradas_vm": DIGESTS_VM,
                 "clientes": normas, "minibatches": list(esperados.values())}
    (saida / "auditoria.json").write_text(json.dumps(resultado, indent=2) + "\n", encoding="utf-8")
    exigir(pesos_iguais and scores_iguais, f"Divergência da referência VM. Consulte {saida / 'auditoria.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artefatos", type=Path)
    parser.add_argument("dados_internos", type=Path)
    parser.add_argument("saida", type=Path)
    args = parser.parse_args()
    retomar(args.artefatos, args.dados_internos, args.saida)
