# Artigo 01 · Rodada 10 limpa reproduzida bit a bit

27/11/2026, 08:49:40, Belém (UTC−03). Objetivo: exportar os dados internos congelados e retomar o FedAvg-SGD da rodada 9 para executar somente a rodada 10. **Os oito tensores de pesos e os 50.815 scores coincidem bit a bit com a VM. Os dois arquivos serializados também coincidem byte a byte com as referências.** [Preparação do ambiente](RELATORIO_2026-11-27_08-34-25_BRT_ambiente_retomada_10_e_fonte.md).

## Entrada e execução

A fonte `/home/kali/Downloads/CICIDS2017_improved.zip` passou na conferência do SHA-256 previsto no protocolo (`97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`). O exportador selecionou somente os IDs congelados e gerou [ajuste_validacao_interna.npz](../../cicids2017-corrigido/ajuste_validacao_interna.npz), 41.205.196 B, SHA-256 `55742f5e280e8e13f26e83bd83d48d541d6cf391128a7cc48bb0f222c75862b5`. A releitura do NPZ confirmou a ordem do manifesto, formas, features float64, rótulos int64 e ausência de IDs do teste cronológico reservado.

| Partição | Forma das features | BENIGN | DDoS |
|---|---:|---:|---:|
| Ajuste | 203.251 × 81 | 163.096 | 40.155 |
| Validação interna | 50.815 × 81 | 40.776 | 10.039 |

A execução em `cnn-flower/.venv-3.14.4` conferiu os quatro hashes da VM, restaurou os pesos da rodada 9, confirmou a normalização de referência e executou a rodada 10 com cinco clientes e seeds 1023–1027. Executou 400 passos locais, distribuídos em 9, 40, 13, 100 e 238. A agregação auditada aceitou os cinco deltas e produziu normas L2 de 0,028684, 0,046987, 0,044385, 0,152830 e 0,271702 por ordem de cliente. Os scores vieram somente da validação interna. O teste reservado não foi materializado nem avaliado. [Auditoria da rodada](retomada-10-auditada/auditoria.json).

## Comparação com a VM

Recarreguei os estados e conferi forma, dtype e bytes de cada um dos oito tensores (1.149 parâmetros). Também comparei os bytes dos 50.815 scores float32. O `cmp` dos arquivos completos retornou sucesso para ambos.

| Saída | SHA-256 do arquivo, igual à VM | SHA-256 do conteúdo numérico |
|---|---|---|
| [rodada-10.pt](retomada-10-auditada/rodada-10.pt) | `8be0ec6a061c77d5c3e806d4c6ca8b3983b514ab89cff374011d392e914808da` | Pesos `a9136e2223be055807caab16958686e4a98fb69ad1b4a0f5bfdffae5bad4924d` |
| [scores_validacao_10.npy](retomada-10-auditada/scores_validacao_10.npy) | `56506368572736c705ac4f94bb4b9c6c4a905fbcea72d858387ceddeb550e198` | Scores `694e1faf25f1d3ccafe728886d403ed5be5821efd2e25f3b89e9a303216781db` |

O [JSON de auditoria](retomada-10-auditada/auditoria.json) tem SHA-256 `6cb85949f8e287f7da3f68dcb1e86295ceb85098b7a507c59c75a40276833d6c` e registra `pesos_bit_a_bit: true` e `scores_bit_a_bit: true`. Nenhuma divergência encontrada. A reprodução da rodada 10 está concluída. Para repetir a conferência, preservar os artefatos atuais e usar destinos novos.

## Comandos e estado do repositório

Comandos de reprodução executados da raiz (os destinos já existem nesta execução):

```sh
set -e
BASE_10=secfednet-local/artigo-01
PYTHON_10="$BASE_10/cnn-flower/.venv-3.14.4/bin/python"
FONTE_10="$HOME/Downloads/CICIDS2017_improved.zip"
ART_10="$HOME/PycharmProjects/SecFedNet-artefatos/fedavg-rodada20"
DADOS_10="$BASE_10/cicids2017-corrigido/ajuste_validacao_interna.npz"
SAIDA_10="$BASE_10/execucoes/2026-11-27/retomada-10-auditada"
printf '%s  %s\n' 97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883 "$FONTE_10" | sha256sum -c -
"$PYTHON_10" -B "$BASE_10/cnn-scaffold/exportar_ajuste_validacao.py" "$FONTE_10" "$DADOS_10"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 FLWR_TELEMETRY_ENABLED=0
export PYTHONPATH="integracao/artigo-01:$BASE_10/cicids2017-corrigido:$BASE_10/cnn-flower:$BASE_10/cnn-flower-entrega:$BASE_10/cnn-flower-clientes:$BASE_10/cnn-fedprox:$BASE_10/cnn-validacao:$BASE_10/cnn-scaffold"
"$PYTHON_10" -B "$BASE_10/cnn-scaffold/retomar_fedavg_10.py" "$ART_10" "$DADOS_10" "$SAIDA_10"
cmp "$SAIDA_10/rodada-10.pt" "$ART_10/rodada-10.pt"
cmp "$SAIDA_10/scores_validacao_10.npy" "$ART_10/scores_validacao_10.npy"
sha256sum "$DADOS_10" "$SAIDA_10/"{rodada-10.pt,scores_validacao_10.npy,auditoria.json}
```

Git inicial/final em `integracao/artigo-01`, HEAD `4cc2727`, com `secfednet-local/artigo-01/INDEX.md` já modificado e `.idea/` já não rastreada. Arquivos gerados: NPZ interno, estado, scores, auditoria e este relatório. Atualizados `INDEX.md` e `STATUS.md`. Código do ensaio e artefatos de entrada preservados. Instrução aplicável `AGENTS.md`, com `.agents/` e `.codex/` vazios. Comandos adicionais de inspeção e conferência: `git status`, `git rev-parse`, `cat`, `rg`, `find`, `ls`, `stat`, `date` no fuso de Belém, Python para verificar o NPZ e os arrays recarregados, verificação de links e `git diff --check`.
