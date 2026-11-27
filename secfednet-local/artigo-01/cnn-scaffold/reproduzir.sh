#!/usr/bin/env bash
set -euo pipefail

# Executar da raiz do repositório. Nunca sobrescreve uma execução anterior.
DESTINO_SCAFFOLD=${1:?Informe uma pasta de saída nova}
BASE_SCAFFOLD=secfednet-local/artigo-01
PYTHON_SCAFFOLD="$BASE_SCAFFOLD/cnn-flower/.venv/bin/python"
test -x "$PYTHON_SCAFFOLD"
if test -e "$DESTINO_SCAFFOLD"; then
    printf 'A pasta de saída já existe: %s\n' "$DESTINO_SCAFFOLD" >&2
    exit 1
fi
mkdir -p -- "$DESTINO_SCAFFOLD"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 FLWR_TELEMETRY_ENABLED=0
export PYTHONPATH="integracao/artigo-01:$BASE_SCAFFOLD/cicids2017-corrigido:$BASE_SCAFFOLD/cnn-flower:$BASE_SCAFFOLD/cnn-flower-entrega:$BASE_SCAFFOLD/cnn-flower-clientes:$BASE_SCAFFOLD/cnn-fedprox:$BASE_SCAFFOLD/cnn-validacao"

"$PYTHON_SCAFFOLD" -B "$BASE_SCAFFOLD/cnn-scaffold/testar_controles.py" testar \
    "$DESTINO_SCAFFOLD/teste_controles" > "$DESTINO_SCAFFOLD/teste_controles.log" 2>&1
"$PYTHON_SCAFFOLD" -B "$BASE_SCAFFOLD/cnn-scaffold/experimentar_scaffold.py" treinar \
    "$DESTINO_SCAFFOLD/execucao" > "$DESTINO_SCAFFOLD/treino.log" 2>&1
"$PYTHON_SCAFFOLD" -B "$BASE_SCAFFOLD/cnn-scaffold/experimentar_scaffold.py" avaliar \
    "$DESTINO_SCAFFOLD/execucao" > "$DESTINO_SCAFFOLD/recarga.log" 2>&1
"$PYTHON_SCAFFOLD" -B - "$DESTINO_SCAFFOLD" <<'PY'
import re
import sys
from pathlib import Path
saida = Path(sys.argv[1])
for log in saida.glob('*.log'):
    log.write_text(re.sub(r'\x1b\[[0-9;]*m', '', log.read_text(encoding='utf-8')), encoding='utf-8')
print((saida / 'execucao/resultados.json').read_text(encoding='utf-8'))
print('Saída:', saida.resolve())
PY
