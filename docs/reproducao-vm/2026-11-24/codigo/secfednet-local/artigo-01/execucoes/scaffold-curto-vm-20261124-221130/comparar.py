"""Compara a reprodução curta com os arquivos e hashes históricos."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ler_json(path):
    return json.loads(path.read_text())


def diferencas(ref, atual, chave=""):
    if isinstance(ref, dict) and isinstance(atual, dict) and ref.keys() == atual.keys():
        return [dif for k in ref for dif in diferencas(ref[k], atual[k], f"{chave}/{k}")]
    if isinstance(ref, list) and isinstance(atual, list) and len(ref) == len(atual):
        return [dif for i, (a, b) in enumerate(zip(ref, atual))
                for dif in diferencas(a, b, f"{chave}/{i}")]
    if ref == atual:
        return []
    return [{"campo": chave, "referencia": ref, "vm": atual}]


base = Path("secfednet-local/artigo-01")
original = base / "cnn-scaffold/ensaio-01"
novo = Path(sys.argv[1])
checks = {}
for linha in (original.parent / "SHA256_ARTEFATOS").read_text().splitlines():
    esperado, caminho = linha.split(maxsplit=1)
    relativo = Path(caminho).relative_to(original)
    arquivo = novo / relativo
    obtido = sha(arquivo) if arquivo.is_file() else None
    checks[str(relativo)] = {"referencia": esperado, "vm": obtido, "igual": esperado == obtido}

config = "execucao/configuracao.json"
relatorio = {
    "manifesto": str(original.parent / "SHA256_ARTEFATOS"),
    "hashes": checks,
    "total_hashes_iguais": sum(v["igual"] for v in checks.values()),
    "configuracao_diferencas": diferencas(ler_json(original / config), ler_json(novo / config)),
    "clientes_npy_iguais": {},
    "metodos": {},
}
with np.load(original / "execucao/clientes.npz", allow_pickle=False) as ref, np.load(
        novo / "execucao/clientes.npz", allow_pickle=False) as atual:
    assert ref.files == atual.files
    relatorio["clientes_npy_iguais"] = {k: bool(np.array_equal(ref[k], atual[k])) for k in ref.files}

resultados = ler_json(novo / "execucao/resultados.json")
metricas_originais_confirmadas = checks["execucao/resultados.json"]["igual"]
if not metricas_originais_confirmadas:
    import validar_mu
    _, _, _, _, _, _, rotulos, _, _ = validar_mu.carregar_ajuste_validacao(
        base / "cicids2017-corrigido", base / "cnn-validacao/particao")

for atual_metricas in resultados["resultados"]:
    metodo = atual_metricas["nome"]
    sub = Path("execucao") / metodo
    ref = np.load(original / sub / "scores_validacao.npy", allow_pickle=False)
    atual = np.load(novo / sub / "scores_validacao.npy", allow_pickle=False)
    assert atual.shape == ref.shape and atual.dtype == ref.dtype
    assert np.isfinite(atual).all() and np.isfinite(ref).all()
    delta = np.abs(ref.astype(np.float64) - atual.astype(np.float64))
    ref_treino = ler_json(original / sub / "treino.json")
    atual_treino = ler_json(novo / sub / "treino.json")
    ref_metricas = atual_metricas if metricas_originais_confirmadas else {
        "nome": metodo,
        "calibrado_validacao": validar_mu.calibrar(ref, rotulos, resultados["teto_fpr"]),
        "limiar_05": validar_mu.medir_fatia(rotulos, ref >= 0.5),
        "scores_sha256": sha(original / sub / "scores_validacao.npy"),
    }
    relatorio["metodos"][metodo] = {
        "scores": {
            "quantidade": int(ref.size),
            "dtype": str(ref.dtype),
            "quantidade_diferente": int(np.count_nonzero(delta)),
            "diferenca_absoluta_maxima": float(delta.max()),
            "diferenca_absoluta_media": float(delta.mean()),
            "bits_iguais": bool(np.array_equal(ref.view(np.uint32), atual.view(np.uint32))),
        },
        "metricas_referencia": ref_metricas,
        "metricas_vm": atual_metricas,
        "metricas_diferencas": diferencas(ref_metricas, atual_metricas),
        "treino_diferencas": diferencas(ref_treino, atual_treino),
    }

print(json.dumps(relatorio, ensure_ascii=False, indent=2))
