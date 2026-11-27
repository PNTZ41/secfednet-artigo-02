"""Verifica se o SHA histórico depende apenas do hash de configuração gravado."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import torch


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


novo = Path(sys.argv[1])
comparacao = json.loads((novo / "comparacao_referencia.json").read_text())
hashes = comparacao["hashes"]
config = hashes["execucao/configuracao.json"]
for metodo in comparacao["metodos"]:
    relativo = f"execucao/{metodo}/checkpoint.pt"
    checkpoint = torch.load(novo / relativo, weights_only=True, map_location="cpu")
    assert checkpoint["configuracao_sha256"] == config["vm"]
    with tempfile.TemporaryDirectory(prefix="secfednet-checkpoint-") as temporario:
        arquivo = Path(temporario) / "checkpoint.pt"
        torch.save(checkpoint, arquivo)
        assert sha(arquivo) == hashes[relativo]["vm"]
        checkpoint["configuracao_sha256"] = config["referencia"]
        torch.save(checkpoint, arquivo)
        obtido = sha(arquivo)
        assert obtido == hashes[relativo]["referencia"]
    print(f"{metodo}: SHA de referência reproduzido alterando só configuracao_sha256 em cópia temporária ({obtido})")
