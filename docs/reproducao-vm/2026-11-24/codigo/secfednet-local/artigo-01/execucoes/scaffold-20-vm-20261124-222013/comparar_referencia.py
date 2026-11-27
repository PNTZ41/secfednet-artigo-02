"""Compara a reprodução de 20 rodadas com os arquivos e hashes históricos."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ler_json(path):
    return json.loads(path.read_text())


def comparar(ref, vm, campo=""):
    if type(ref) is type(vm):
        if isinstance(ref, dict) and ref.keys() == vm.keys():
            return [d for k in ref for d in comparar(ref[k], vm[k], f"{campo}/{k}")]
        if isinstance(ref, list) and len(ref) == len(vm):
            return [d for i, (a, b) in enumerate(zip(ref, vm, strict=True))
                    for d in comparar(a, b, f"{campo}/{i}")]
        if ref == vm:
            return []
    return [{"campo": campo, "referencia": ref, "vm": vm}]


def ler_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


base = Path("secfednet-local/artigo-01/cnn-scaffold")
referencia = base / "ensaio-20-rodadas"
novo = Path(sys.argv[1])
ref_exec, vm_exec = referencia / "execucao", novo / "execucao"
manifesto = base / "SHA256_ARTEFATOS_20"
hashes = {}
for linha in manifesto.read_text().splitlines():
    esperado, caminho = linha.split(maxsplit=1)
    arquivo_ref = Path(caminho)
    relativo = arquivo_ref.relative_to(referencia).as_posix()
    arquivo = novo / relativo
    local_ref = arquivo_ref.is_file()
    if local_ref:
        assert sha256(arquivo_ref) == esperado, arquivo_ref
    obtido = sha256(arquivo) if arquivo.is_file() else None
    hashes[relativo] = {"referencia": esperado, "referencia_disponivel": local_ref, "vm": obtido,
                       "igual": esperado == obtido}

jsons = {}
csvs = {}
for arquivo in sorted(ref_exec.rglob("*")):
    relativo = arquivo.relative_to(ref_exec)
    if arquivo.suffix == ".json":
        jsons[str(relativo)] = comparar(ler_json(arquivo), ler_json(vm_exec / relativo))
    elif arquivo.suffix == ".csv":
        ref_csv, vm_csv = ler_csv(arquivo), ler_csv(vm_exec / relativo)
        csvs[str(relativo)] = {"linhas_referencia": len(ref_csv), "linhas_vm": len(vm_csv),
                              "diferencas": comparar(ref_csv, vm_csv)}

metodos = {}
for metodo in ("fedavg_sgd", "scaffold"):
    ref_curva = ler_json(ref_exec / metodo / "curva.json")
    ref_rodadas = ler_json(ref_exec / metodo / "rodadas.json")
    vm_curva = ler_json(vm_exec / metodo / "curva.json")
    vm_rodadas = ler_json(vm_exec / metodo / "rodadas.json")
    assert all(len(serie) == 20 for serie in (ref_curva, ref_rodadas, vm_curva, vm_rodadas))
    prefixo = f"execucao/{metodo}"
    estados = []
    for r, (estado_ref, estado_vm, curva_ref, curva_vm) in enumerate(
            zip(ref_rodadas, vm_rodadas, ref_curva, vm_curva, strict=True), start=1):
        arquivo_estado = hashes[f"{prefixo}/rodada-{r:02d}.pt"]
        arquivo_scores = hashes[f"{prefixo}/scores_validacao_{r:02d}.npy"]
        assert arquivo_estado["vm"] == estado_vm["estado_sha256"]
        assert arquivo_estado["referencia"] == estado_ref["estado_sha256"]
        assert arquivo_scores["vm"] == curva_vm["scores_sha256"]
        assert arquivo_scores["referencia"] == curva_ref["scores_sha256"]
        estados.append({
            "rodada": r,
            "arquivo_estado_igual": arquivo_estado["igual"],
            "pesos_iguais": estado_ref["pesos_sha256"] == estado_vm["pesos_sha256"],
            "controle_global_igual": estado_ref["c_sha256"] == estado_vm["c_sha256"],
            "controles_locais_iguais": all(
                a["ci_final_sha256"] == b["ci_final_sha256"]
                for a, b in zip(estado_ref["clientes"], estado_vm["clientes"], strict=True)
            ),
            "scores_iguais": arquivo_scores["igual"],
        })
    metodos[metodo] = {"estado_inicial_igual": hashes[f"{prefixo}/rodada-00.pt"]["igual"],
                       "rodadas": estados, "ponto_final_vm": vm_curva[-1]}

config = hashes["execucao/configuracao.json"]
import torch

for metodo, comparacao in metodos.items():
    relativo = f"execucao/{metodo}/checkpoint.pt"
    checkpoint = torch.load(novo / relativo, weights_only=True, map_location="cpu")
    assert checkpoint["configuracao_sha256"] == config["vm"]
    with tempfile.TemporaryDirectory(prefix="secfednet-20-checkpoint-") as tmp:
        arquivo = Path(tmp) / "checkpoint.pt"
        torch.save(checkpoint, arquivo)
        sha_reserializado = sha256(arquivo)
        checkpoint["configuracao_sha256"] = config["referencia"]
        torch.save(checkpoint, arquivo)
        sha_config_historica = sha256(arquivo)
    comparacao["checkpoint"] = {
        "resserializacao_identica_ao_da_vm": sha_reserializado == hashes[relativo]["vm"],
        "sha256_com_configuracao_historica": sha_config_historica,
        "reproduz_sha_historico_alterando_apenas_hash_da_configuracao":
            sha_config_historica == hashes[relativo]["referencia"],
    }

print(json.dumps({"manifesto_historico": str(manifesto), "hashes": hashes,
                  "diferencas_json": jsons, "comparacao_csv": csvs, "metodos": metodos},
                 indent=2, ensure_ascii=False))
