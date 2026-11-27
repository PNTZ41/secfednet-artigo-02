#!/usr/bin/env bash
set -euo pipefail

DESTINO_20=${1:?Informe uma pasta de saída nova}
BASE_20=secfednet-local/artigo-01
PYTHON_20="$BASE_20/cnn-flower/.venv/bin/python"
test -x "$PYTHON_20"
if test -e "$DESTINO_20"; then
    printf 'A pasta de saída já existe: %s\n' "$DESTINO_20" >&2
    exit 1
fi
mkdir -p -- "$DESTINO_20"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 FLWR_TELEMETRY_ENABLED=0
export PYTHONPATH="integracao/artigo-01:$BASE_20/cicids2017-corrigido:$BASE_20/cnn-flower:$BASE_20/cnn-flower-entrega:$BASE_20/cnn-flower-clientes:$BASE_20/cnn-fedprox:$BASE_20/cnn-validacao:$BASE_20/cnn-scaffold"
"$PYTHON_20" -B "$BASE_20/cnn-scaffold/testar_controles.py" testar \
    "$DESTINO_20/teste_controles" > "$DESTINO_20/teste_controles.log" 2>&1
"$PYTHON_20" -B "$BASE_20/cnn-scaffold/experimentar_20.py" treinar \
    "$DESTINO_20/execucao" > "$DESTINO_20/treino.log" 2>&1
"$PYTHON_20" -B "$BASE_20/cnn-scaffold/experimentar_20.py" verificar \
    "$DESTINO_20/execucao" > "$DESTINO_20/verificacao.log" 2>&1
"$PYTHON_20" -B - "$DESTINO_20" <<'PY'
import json
import re
import sys
from pathlib import Path
p = Path(sys.argv[1])
for log in p.glob('*.log'):
    log.write_text(re.sub(r'\x1b\[[0-9;]*m', '', log.read_text(encoding='utf-8')), encoding='utf-8')
comparacoes = json.loads((p / 'execucao/comparacoes.json').read_bytes())
for par in comparacoes['pares']:
    print('Comparação:', par['eixo'])
    for k in ('fedavg', 'scaffold'):
        r = par[k]
        v = r['validacao_calibrada']
        print(r['metodo'], r['rodada'], 'recall', v['recall_ddos'], 'FP', v['matriz_real_por_previsto'][0][1],
              'FPR', v['fpr'], 'bytes', r['bytes_brutos_acumulados'])
print('Saída:', p.resolve())
PY
