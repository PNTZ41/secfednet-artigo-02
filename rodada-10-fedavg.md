# Reprodução da rodada 10 limpa do FedAvg-SGD

**Os oito tensores de pesos da CNN (1.149 parâmetros) e as 50.815 pontuações da validação interna coincidiram bit a bit com a VM.** Em 27/11/2026, uma segunda conferência com `cmp` confirmou a igualdade dos dois arquivos completos, inclusive dos bytes de serialização.

## O que foi reproduzido

O ensaio BENIGN × DDoS usa uma CNN unidimensional com 81 atributos. A retomada restaurou os pesos de `rodada-09.pt` e conferiu a média, a escala e a ordem das colunas com `checkpoint.pt`. O exportador seguiu os IDs do manifesto original, na mesma ordem. Os IDs do teste cronológico reservado ficaram fora da exportação.

| Partição | Fluxos | BENIGN | DDoS |
|---|---:|---:|---:|
| Ajuste | 203.251 | 163.096 | 40.155 |
| Validação interna | 50.815 | 40.776 | 10.039 |

A referência usou Python 3.14.4, PyTorch 2.12.1+cpu, Flower 1.32.0 e NumPy 2.3.5. Os cinco clientes seguiram a partição original (seed 2305), com uma época de SGD, taxa 0,01 e lotes de até 512 exemplos. O servidor aplicou a média uniforme dos cinco deltas de pesos. Essa regra identifica o comparador usado neste ensaio.

| Cliente | Seed da rodada | Passos locais | Norma L2 do delta |
|---:|---:|---:|---:|
| 0 | 1023 | 9 | 0,028684 |
| 1 | 1024 | 40 | 0,046987 |
| 2 | 1025 | 13 | 0,044385 |
| 3 | 1026 | 100 | 0,152830 |
| 4 | 1027 | 238 | 0,271702 |

## Auditoria do servidor

A rotina de retomada confere participantes, quantidade de tensores, dimensões, tipo e finitude antes de chamar a agregação original. Calcula a norma L2 em float64 por cliente e verifica a finitude dos pesos agregados. Nos testes sintéticos registrados, contribuições com quantidade, forma ou tipo incorretos, NaN ou infinito foram rejeitadas. As contribuições válidas produziram a mesma agregação do controle. A rodada real confirmou a preservação do resultado no caminho de retomada com os cinco clientes válidos.

As cinco normas descrevem uma única rodada limpa. Para avaliar um limiar de anomalia, ainda faltam a distribuição das normas em outras rodadas limpas e uma estimativa dos falsos alarmes. Para testar o comportamento em caso de falha no fluxo completo, o próximo ensaio defensivo pode verificar se a rejeição preserva o último checkpoint válido.

## Evidências para conferência

| Arquivo | SHA-256 |
|---|---|
| `rodada-09.pt` da VM | `2bd04013797041c291013ac82c32ad2e25ce3e8110b5d80f24cf97bf1ffdd062` |
| `checkpoint.pt` da VM | `4e73b24cf7042eace103969787d86f07084ddc4eb558a01fe3bcf32562898922` |
| `ajuste_validacao_interna.npz` | `55742f5e280e8e13f26e83bd83d48d541d6cf391128a7cc48bb0f222c75862b5` |
| `rodada-10.pt` da VM e da retomada | `8be0ec6a061c77d5c3e806d4c6ca8b3983b514ab89cff374011d392e914808da` |
| `scores_validacao_10.npy` da VM e da retomada | `56506368572736c705ac4f94bb4b9c6c4a905fbcea72d858387ceddeb550e198` |

No acervo SecFedNet, os parâmetros por cliente estão em `secfednet-local/artigo-01/execucoes/2026-11-27/retomada-10-auditada/auditoria.json`. O relatório original da mesma pasta de data, `RELATORIO_2026-11-27_08-49-40_BRT_retomada_10_reproduzida.md`, documenta a exportação e o comando de treino. Para repetir somente a comparação, a partir da raiz do projeto original com os artefatos disponíveis, execute o bloco abaixo. O código de saída zero de cada comparação indica igualdade completa.

```sh
set -e
saida=secfednet-local/artigo-01/execucoes/2026-11-27/retomada-10-auditada
vm=../SecFedNet-artefatos/fedavg-rodada20
cmp "$saida/rodada-10.pt" "$vm/rodada-10.pt"
cmp "$saida/scores_validacao_10.npy" "$vm/scores_validacao_10.npy"
```
