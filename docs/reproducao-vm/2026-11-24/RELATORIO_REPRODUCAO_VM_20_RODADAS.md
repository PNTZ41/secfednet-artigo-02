# SecFedNet · Reprodução de 20 rodadas na VM

Execução na VM `secfednet-repro` iniciada em 24/11/2026 às 22:20:13 BRT (America/Belem, UTC−03:00). Reproduzi o ensaio de 20 rodadas FedAvg-SGD × SCAFFOLD no commit `0b38f255af6f22e4642c584c0f0e09b15ef9263e` com `reproduzir_20.sh`. Usei o CICIDS2017 corrigido e o ambiente de treino já instalados, com os hiperparâmetros originais. A avaliação usou somente a validação interna congelada.

## Resultados e comunicação

As 40 linhas dos CSVs de curvas, as métricas finais, os volumes de comunicação por rodada e acumulados, e a instrumentação das rodadas coincidiram com a referência versionada. As curvas incluem BCE global e online nas duas ponderações, limiar, recall, FPR, FP, macro-F1, passos e exposições. Na rodada 20, a BCE global uniforme por cliente foi 0,157336287 para FedAvg-SGD e 0,288662023 para SCAFFOLD. Ponderada por exemplo, foi 0,193955701 e 0,363439357, respectivamente.

| Método e rodada | Limiar | Recall DDoS | FPR | Macro-F1 | Matriz [[VN, FP], [FN, VP]] |
| --- | ---: | ---: | ---: | ---: | ---: |
| FedAvg-SGD 20 | 0,365105987 | 99,1633% | 0,995684% | 0,984974069 | [[40370, 406], [84, 9955]] |
| SCAFFOLD 20 | 0,210269406 | 74,7186% | 0,998136% | 0,900356695 | [[40369, 407], [2538, 7501]] |
| SCAFFOLD 10 | 0,187195152 | 0,2690% | 0,995684% | 0,445435760 | [[40370, 406], [10012, 27]] |

A validação tinha 40.776 BENIGN e 10.039 DDoS. O limiar de cada ponto foi escolhido nessa mesma validação com FPR ≤ 1%, portanto as métricas são exploratórias. No limiar fixo de 0,5, o FedAvg-SGD na rodada 20 obteve 12,6307% de recall, 4 FP e macro-F1 0,563525444. O SCAFFOLD na rodada 20 classificou toda a validação como BENIGN, com recall zero, 0 FP e macro-F1 0,445196580.

| Método e rodada | Bytes parâmetros | Bytes controles | Bytes totais | Passos | Exposições |
| --- | ---: | ---: | ---: | ---: | ---: |
| FedAvg-SGD 20 | 919.200 | 0 | 919.200 | 8.000 | 4.065.020 |
| SCAFFOLD 20 | 919.200 | 919.200 | 1.838.400 | 8.000 | 4.065.020 |
| SCAFFOLD 10 | 459.600 | 459.600 | 919.200 | 4.000 | 2.032.510 |

Os bytes somam subida e descida dos arrays float32 da simulação em processo. Em 20 contra 20 rodadas, o SCAFFOLD teve 24,4447 pontos percentuais a menos de recall e consumiu o dobro do volume bruto. Com o mesmo volume de 919.200 bytes, o SCAFFOLD na rodada 10 teve 98,8943 pontos percentuais a menos de recall e a mesma taxa de falsos positivos. As três linhas coincidiram com os pontos fixados no protocolo histórico.

## Estados e diferenças

- **42 de 42 estados** das rodadas 0–20, contando os dois métodos, e **40 de 40 arquivos de scores** por rodada reproduziram os SHA-256 históricos. Os hashes de pesos e controles globais e locais coincidiram em cada rodada. A comparação usou os manifestos históricos para os binários incluídos na entrega apenas por hash e os JSONs versionados para conferir os campos por rodada.
- O script recarregou os 40 estados pós-treino em outro processo, verificou os dois checkpoints finais e reproduziu os scores bit a bit. O teste escalar, o pareamento e a reprodução das duas primeiras rodadas contra a referência curta também passaram.
- Dos 113 itens de `SHA256_ARTEFATOS_20`, 101 tiveram SHA-256 idêntico e 9 divergiram. Os três históricos sem saída correspondente, `execucao/auditoria_curvas.json`, `fontes.log` e `preservacao.log`, estão fora das saídas do wrapper. A comparação desta execução e as checagens de fontes e preservação foram registradas separadamente.
- O único campo diferente em `configuracao.json` foi `versoes.plataforma`. O kernel passou de `7.0.0-43-generic` na referência para `7.0.0-44-generic` na VM. Em cópias temporárias dos checkpoints, substituir apenas `configuracao_sha256` pelo valor histórico reproduziu os dois SHA-256 históricos dos checkpoints.
- As curvas JSON e `comparacoes.json` diferiram exclusivamente em `tempo_monitoramento_s`. Os dois `treino.json` diferiram apenas em `tempo_treino_s` e `checkpoint_sha256`. A última diferença foi `tempo.json`. Os dois `rodadas.json`, os três CSVs, `resultados.json`, `pareamento.json` e `verificacao_independente.json` coincidiram.

## Ambiente e tempos

Ubuntu 26.04.1 LTS, Linux 7.0.0-44-generic x86-64, glibc 2.43, Intel Core i3-10100 com quatro CPUs visíveis. CPython 3.14.4, PyTorch 2.12.1+cpu, Flower 1.32.0 e NumPy 2.3.5. O `uv` 0.13.10 confirmou a compatibilidade dos 41 pacotes já instalados. O ZIP de 343.549.013 bytes passou na verificação do SHA-256 `97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`.

| Medida | VM | Referência |
| --- | ---: | ---: |
| FedAvg-SGD, treino e monitoramento | 43,127 s | 33,517 s |
| SCAFFOLD, treino e monitoramento | 42,703 s | 34,413 s |
| Monitoramento dentro do tempo FedAvg-SGD | 11,307 s | 8,836 s |
| Monitoramento dentro do tempo SCAFFOLD | 10,902 s | 8,889 s |
| Fase de treino completa, conforme `execucao/tempo.json` | 103,320 s | 84,792 s |
| Wrapper completo, incluindo teste escalar e verificação independente | 156,42 s | — |
| Pico de RSS do wrapper, conforme GNU time | 1.146.672 KiB (≈1,09 GiB) | — |

O GNU time mediu 235,98 s de CPU em modo usuário e 3,56 s em modo sistema. Os valores históricos versionados incluem os tempos internos de treino, sem medida equivalente de pico de RSS ou de tempo do wrapper completo.

## Comandos e artefatos

A partir de `/home/williian/secfednet-repro/codigo`. Na execução medida, o arquivo do GNU time ficou em `/tmp` até o wrapper criar o destino novo.

```bash
set -e
git status --short --branch --untracked-files=all
git rev-parse HEAD
cat AGENTS.md README.md
base=secfednet-local/artigo-01
cat "$base/cnn-scaffold/README_20.md"
sha256sum -c SHA256_ENTREGA --quiet
sha256sum -c "$base/cnn-scaffold/SHA256_FONTES_20" --quiet
printf '%s  %s\n' 97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883 \
  "$base/cicids2017-corrigido/CICIDS2017_improved.zip" | sha256sum -c
UV_CACHE_DIR=/tmp/secfednet-uv-cache uv --no-config pip check \
  --python "$base/cnn-flower/.venv/bin/python"

reg="$base/execucoes"
destino="$reg/scaffold-20-vm-$(TZ=America/Belem date +%Y%m%d-%H%M%S)"
marca="${destino##*/}"
find "$reg/scaffold-curto-vm-20261124-221130" -type f -print0 |
  sort -z | xargs -0 sha256sum > "/tmp/$marca-curto.sha256"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
/usr/bin/time -v -o "/tmp/$marca-tempo.txt" \
  bash "$base/cnn-scaffold/reproduzir_20.sh" "$destino"
cp -- "/tmp/$marca-tempo.txt" "$destino/tempo-processo.txt"
sha256sum -c "/tmp/$marca-curto.sha256" --quiet
```

Para repetir a comparação desta execução:

```bash
base=secfednet-local/artigo-01
destino=secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
"$base/cnn-flower/.venv/bin/python" -B "$destino/comparar_referencia.py" "$destino"
sha256sum -c "$destino/preservacao-execucao-curta.sha256" --quiet
sha256sum -c "$base/cnn-scaffold/SHA256_FONTES_20" --quiet
sha256sum -c SHA256_ENTREGA --quiet
git status --short --branch --untracked-files=all
```

- [Pasta nova](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013) · [Curvas CSV](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/execucao/curvas.csv) · [Métricas finais](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/execucao/resultados.json) · [Comparações 20/20 e 20/10](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/execucao/comparacoes.json).
- [Comparação com a referência por arquivo, campo e rodada](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/comparacao_referencia.json) · [Verificação independente](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/execucao/verificacao_independente.json) · [Log da verificação](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/verificacao.log) · [Tempo e RSS](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/tempo-processo.txt).
- [Hashes da execução curta preservada](codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/preservacao-execucao-curta.sha256). Os 33 arquivos conferiram após o ensaio. O relatório curto também foi conferido contra sua cópia local.

## Estado final

HEAD destacado e limpo no commit `0b38f25` no início e no fim. Os 89 arquivos do manifesto de entrega e as entradas de `SHA256_FONTES_20` passaram antes e depois. Foram criados a pasta de saída, o script e o JSON locais de comparação, as evidências de tempo e preservação e os registros Markdown. Os arquivos versionados, a entrega de Gabriel e a execução anterior foram preservados. O índice e o status locais ficam em `secfednet-local/artigo-01/execucoes/`, preservando o índice versionado. Nenhum stage, commit ou push foi efetuado.

A instrução local encontrada foi `/home/williian/secfednet-repro/codigo/AGENTS.md`. As pastas `.agents/` e `.codex/` do repositório estavam vazias. A busca local encontrou somente esse arquivo de instruções e nenhuma skill local aplicável. Nenhum subagente foi usado.

Sem pendências de execução ou bloqueios. Próximo passo de revisão: anexar `/home/williian/secfednet-repro/RELATORIO_REPRODUCAO_VM_20_RODADAS.md`.

