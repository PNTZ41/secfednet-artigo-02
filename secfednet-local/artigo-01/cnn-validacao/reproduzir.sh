#!/usr/bin/env bash
set -euo pipefail

# Execute da raiz do repositório, informando uma pasta de saída ainda inexistente.
DESTINO_VALIDACAO=${1:?Informe a pasta de saída nova}
BASE_VALIDACAO=secfednet-local/artigo-01
PYTHON_VALIDACAO="$BASE_VALIDACAO/cnn-flower/.venv/bin/python"
if test -e "$DESTINO_VALIDACAO"; then
    printf 'A pasta de saída já existe: %s\n' "$DESTINO_VALIDACAO" >&2
    exit 1
fi
test -x "$PYTHON_VALIDACAO"
mkdir -p -- "$DESTINO_VALIDACAO"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 FLWR_TELEMETRY_ENABLED=0
export PYTHONPATH="integracao/artigo-01:$BASE_VALIDACAO/cicids2017-corrigido:$BASE_VALIDACAO/cnn-flower:$BASE_VALIDACAO/cnn-flower-entrega:$BASE_VALIDACAO/cnn-flower-clientes:$BASE_VALIDACAO/cnn-fedprox"

"$PYTHON_VALIDACAO" -B "$BASE_VALIDACAO/cnn-validacao/validar_mu.py" preparar \
    "$BASE_VALIDACAO/cicids2017-corrigido" "$BASE_VALIDACAO/cnn-validacao/protocolo.json" \
    "$DESTINO_VALIDACAO/particao" > "$DESTINO_VALIDACAO/preparacao.log" 2>&1
"$PYTHON_VALIDACAO" -B "$BASE_VALIDACAO/cnn-validacao/validar_mu.py" treinar \
    "$BASE_VALIDACAO/cicids2017-corrigido" "$DESTINO_VALIDACAO/particao" \
    "$DESTINO_VALIDACAO/execucao" > "$DESTINO_VALIDACAO/treino.log" 2>&1

"$PYTHON_VALIDACAO" -B - "$DESTINO_VALIDACAO" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
for nome in ("preparacao.log", "treino.log"):
    caminho = root / nome
    caminho.write_text(re.sub(r"\x1b\[[0-9;]*m", "", caminho.read_text(encoding="utf-8")), encoding="utf-8")
selecao = json.loads((root / "execucao/selecao.json").read_bytes())
print("Selecionado na validação:", selecao["escolhido"], "limiar", selecao["limiar"])
print("Saída:", root.resolve())
PY
