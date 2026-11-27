#!/usr/bin/env bash
set -euo pipefail

destino_candidato=${1:?Informe uma pasta de execução nova}
python_candidato=${2:?Informe o Python do lock requirements.lock}
zip_candidato=${3:?Informe CICIDS2017_improved.zip externo}
scripts_candidato=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
test ! -e "$destino_candidato"
mkdir -p -- "$destino_candidato"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 FLWR_TELEMETRY_ENABLED=0
unset PYTHONPATH
"$python_candidato" -B "$scripts_candidato/baseline.py" testar > "$destino_candidato/testes_metricas.log" 2>&1
"$python_candidato" -B "$scripts_candidato/preparar_candidato.py" "$zip_candidato" "$destino_candidato/candidato" > "$destino_candidato/preparo.log" 2>&1
"$python_candidato" -B "$scripts_candidato/documentar_candidato.py" "$destino_candidato/candidato" > "$destino_candidato/documentacao.log" 2>&1
"$python_candidato" -B "$scripts_candidato/verificar_candidato.py" "$destino_candidato/candidato" > "$destino_candidato/verificacao.log" 2>&1
"$python_candidato" -B "$scripts_candidato/baseline.py" treinar "$destino_candidato/candidato" "$scripts_candidato/baseline_config.json" "$destino_candidato/baseline" > "$destino_candidato/baseline.log" 2>&1
"$python_candidato" -B "$scripts_candidato/baseline.py" verificar "$destino_candidato/candidato" "$destino_candidato/baseline" > "$destino_candidato/baseline_recarga.log" 2>&1
"$python_candidato" -B "$scripts_candidato/federado_integracao.py" treinar "$destino_candidato/candidato" "$destino_candidato/fedavg_integracao" > "$destino_candidato/flower.log" 2>&1
"$python_candidato" -B "$scripts_candidato/federado_integracao.py" verificar "$destino_candidato/candidato" "$destino_candidato/fedavg_integracao" > "$destino_candidato/flower_recarga.log" 2>&1
