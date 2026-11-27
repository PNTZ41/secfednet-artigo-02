> Cópia editorial de evidência histórica, com links adaptados. Os manifestos históricos referem-se aos bytes originais do acervo; confira esta seleção com [SHA256_EXPERIMENTOS](../SHA256_EXPERIMENTOS). Veja a [entrada de reprodução](../README.md).

# SecFedNet · rodada limitada na VM

Estado: **concluida**. Início 2026-11-25T21:23:01.660873-03:00; fim 2026-11-25T21:31:34.839594-03:00. Limite externo 45 min, reserva interna de 1 min para finalizar. Execução detached (`nohup`/nova sessão) com status/log persistentes. Etapas concluídas: 01_venv, 02_lock_offline, 02c_pip_check, 03_reproducao, 04_gate_reproducao, 05_seed23_central, 05_seed23_fedavg, 05_seed41_central, 05_seed41_fedavg, 05_seed89_central, 05_seed89_fedavg.

Raiz VM: `/home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/2026-11-25/rodada-limitada-21-11-59`. Relatório: `/home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/2026-11-25/rodada-limitada-21-11-59/RELATORIO_2026-11-25_21-31-34_BRT_VM_CNN_5x5.md`. Ambiente e identidade: VM secfednet-repro, MAC 52:54:00:16:cd:d7, 192.168.122.8; recursos iniciais em manifesto. Git histórico inicial/final: `0b38f255af6f22e4642c584c0f0e09b15ef9263e`, preservado=True; stage inicial/final vazio=True. Novas saídas locais ignoradas, sem commit/push/PR. Configurações globais e aplicativos existentes preservados.

## Reprodução antes da comparação

ZIP corrigido reutilizado na VM, SHA `97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`. Ambiente novo reconstruído pelo lock, sem alterar o antigo. `reproduzir.sh` foi executado com destino novo. Gate numérico contra Kubuntu: **True**, tolerância zero para índices, contagens, parâmetros/matrizes, pesos, scores/métricas da quinta e recargas. Fonte de referência: execução Kubuntu `protocolo-candidato-validacao-20-46-58`.

Variações de tempo/pico e hashes de checkpoint vinculados ao manifesto específico da execução são separadas de divergências numéricas. Campo a campo no manifesto e tabela de checks. Nenhuma comparação pareada é autorizada pelo runner sem o gate passar. Versões e logs da reconstrução: `logs/`.

## Protocolo e comparação exploratória

BENIGN=0, ATTACK=1; rótulos nominais preservados. Treino segunda–quarta 1.184.424; quinta principal 360.078 e sensibilidade bruta 328.429; sexta reservada, usada apenas nas verificações do manifesto/qualidade/interseções. Sexta **sem previsões ou métricas de desempenho**. Normalização float64 só do treino, entrada float32; mesmas máscaras por par. Sensibilidade bruta ainda contém 44/46/9 chaves compartilhadas após transformação float32 nos três pares; não houve expurgo adicional nem protocolo final congelado.

Seeds 23/41/89; partição 2305/4105/8905. CNN-1D idêntica, mesmos pesos iniciais por par, Adam lr=0,001, betas=(0,9;0,999), eps=1e-8, weight_decay=0, lote 512, limiar fixo 0,5. Cinco épocas centralizadas vs cinco rodadas FedAvg com época local única, cinco clientes, participação integral, Dirichlet α=0,5. Adam reinicia por época central e por cliente/rodada federada. Global shuffle no central e embaralhamento local no FedAvg: minibatches não são idênticos; tamanho e seeds estão fixados. Torch dois threads/interop um; treinos em processos sequenciais. A reprodução mantém os caps BLAS/OMP do roteiro histórico; comparação limitada a dois.

PR-AUC reportada como **average precision**, soma Δrecall×precision com empates agrupados, positivo ATTACK, sem trapézios. Sem calibração na quinta, sem ajuste na sexta. Tipos ausentes: recall NA; BENIGN por tipo é especificidade. A quinta é dominada por Infiltration - Portscan (99,805% dos positivos). Três seeds medem variação conjunta de inicialização, minibatches e partição, não isolam suas causas. Resultados exploratórios de uma captura/validação; sem inferência de significância ou generalização externa.

| Seed | Método | Quinta | AP | Macro-F1 | Recall ATTACK | FPR | Matriz [[VN,FP],[FN,VP]] |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 23 | central | principal | 0.673941 | 0.513220 | 0.070118 | 0.000663 | [[287980,191],[66865,5042]] |
| 23 | central | sensibilidade_raw64 | 0.683973 | 0.507527 | 0.070118 | 0.000745 | [[256331,191],[66865,5042]] |
| 23 | fedavg | principal | 0.704860 | 0.535288 | 0.094636 | 0.000746 | [[287956,215],[65102,6805]] |
| 23 | fedavg | sensibilidade_raw64 | 0.709913 | 0.529710 | 0.094636 | 0.000838 | [[256307,215],[65102,6805]] |
| 41 | central | principal | 0.552378 | 0.443488 | 0.000292 | 0.005452 | [[286600,1571],[71886,21]] |
| 41 | central | sensibilidade_raw64 | 0.565498 | 0.437325 | 0.000292 | 0.006124 | [[254951,1571],[71886,21]] |
| 41 | fedavg | principal | 0.548657 | 0.463021 | 0.017995 | 0.000264 | [[288095,76],[70613,1294]] |
| 41 | fedavg | sensibilidade_raw64 | 0.556468 | 0.457094 | 0.017995 | 0.000296 | [[256446,76],[70613,1294]] |
| 89 | central | principal | 0.490472 | 0.490361 | 0.048132 | 0.005920 | [[286465,1706],[68446,3461]] |
| 89 | central | sensibilidade_raw64 | 0.507183 | 0.484407 | 0.048132 | 0.006651 | [[254816,1706],[68446,3461]] |
| 89 | fedavg | principal | 0.461353 | 0.451133 | 0.006369 | 0.000177 | [[288120,51],[71449,458]] |
| 89 | fedavg | sensibilidade_raw64 | 0.469008 | 0.445155 | 0.006369 | 0.000199 | [[256471,51],[71449,458]] |

Suporte principal: BENIGN 288.171 / ATTACK 71.907. Sensibilidade: BENIGN 256.522 / ATTACK 71.907. [Resultados e matrizes](tabelas/resultados_por_seed.csv) · [recall/suporte por tipo e seed](tabelas/recall_por_tipo.csv).

### Orçamento efetivo

| Seed | Método | Exposições | Passos Adam | Treino s | Pico RSS KiB |
| --- | --- | ---: | ---: | ---: | ---: |
| 23 | central | 5922120 | 11570 | 48.391 | 914112 |
| 23 | fedavg | 5922120 | 11580 | 46.268 | 1164692 |
| 41 | central | 5922120 | 11570 | 48.160 | 913708 |
| 41 | fedavg | 5922120 | 11580 | 47.863 | 1164468 |
| 89 | central | 5922120 | 11570 | 49.034 | 913668 |
| 89 | fedavg | 5922120 | 11575 | 48.331 | 1165328 |

Exposições iguais por par; passos podem diferir pelas caudas dos minibatches de cada cliente. Estatísticas Adam são segregadas por cliente no FedAvg; trajetórias não são equivalentes. Hashes de inicialização/partição/máscaras pareados são conferidos. [Orçamento completo](tabelas/orcamento_por_seed.csv).

### Variação entre seeds (média ± desvio amostral)

| Método | Quinta | Métrica | N | Média | DP (ddof=1) | Mínimo | Máximo |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| central | principal | AP | 3 | 0.572264 | 0.093337 | 0.490472 | 0.673941 |
| central | principal | macro_F1 | 3 | 0.482356 | 0.035548 | 0.443488 | 0.513220 |
| central | principal | recall_ATTACK | 3 | 0.039514 | 0.035702 | 0.000292 | 0.070118 |
| central | principal | FPR | 3 | 0.004012 | 0.002910 | 0.000663 | 0.005920 |
| central | sensibilidade_raw64 | AP | 3 | 0.585552 | 0.090085 | 0.507183 | 0.683973 |
| central | sensibilidade_raw64 | macro_F1 | 3 | 0.476420 | 0.035776 | 0.437325 | 0.507527 |
| central | sensibilidade_raw64 | recall_ATTACK | 3 | 0.039514 | 0.035702 | 0.000292 | 0.070118 |
| central | sensibilidade_raw64 | FPR | 3 | 0.004506 | 0.003268 | 0.000745 | 0.006651 |
| fedavg | principal | AP | 3 | 0.571623 | 0.123367 | 0.461353 | 0.704860 |
| fedavg | principal | macro_F1 | 3 | 0.483147 | 0.045545 | 0.451133 | 0.535288 |
| fedavg | principal | recall_ATTACK | 3 | 0.039667 | 0.047958 | 0.006369 | 0.094636 |
| fedavg | principal | FPR | 3 | 0.000396 | 0.000307 | 0.000177 | 0.000746 |
| fedavg | sensibilidade_raw64 | AP | 3 | 0.578463 | 0.121949 | 0.469008 | 0.709913 |
| fedavg | sensibilidade_raw64 | macro_F1 | 3 | 0.477320 | 0.045762 | 0.445155 | 0.529710 |
| fedavg | sensibilidade_raw64 | recall_ATTACK | 3 | 0.039667 | 0.047958 | 0.006369 | 0.094636 |
| fedavg | sensibilidade_raw64 | FPR | 3 | 0.000444 | 0.000344 | 0.000199 | 0.000838 |

[Tabela completa](tabelas/variacao_entre_seeds.csv). Estado/pendência: rodada concluída; revisar protocolo antes de sexta. Última etapa: todas_as_seeds_concluidas. Modelos/caches/scores permanecem somente na VM; o retorno contém relatório, tabelas, logs sanitizados e manifesto. Nenhum artefato histórico foi sobrescrito.

## Acompanhamento e reprodução

```bash
ssh williian@192.168.122.8 'cat /home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/2026-11-25/rodada-limitada-21-11-59/STATUS.json'
ssh williian@192.168.122.8 'tail -F /home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/2026-11-25/rodada-limitada-21-11-59/execucao.log'
```

O log da etapa ativa está em `log_atual` do STATUS; durante a reprodução, consultar também `/home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/2026-11-25/rodada-limitada-21-11-59/reproducao/preparo.log`. O supervisor sobrevive ao fechamento do terminal. Comandos exatos e configurações imutáveis constam no manifesto. Para repetir, usar pasta nova, mesmo lock/dataset/fontes e inicializar o supervisor com limite externo de 2700 s. Não reutilizar destinos existentes.

Instruções consultadas no Kubuntu e na VM: AGENTS.md do projeto; skill local secfednet-validar-experimento na sessão principal. Nenhum subagente. Recursos .agents/.codex globais preservados. Próximo passo: revisar resultados e política de colisões; desempenho da sexta permanece pendente.
