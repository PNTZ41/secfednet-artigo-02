> Cópia editorial de evidência histórica, com links adaptados. Os manifestos históricos referem-se aos bytes originais do acervo; confira esta seleção com [SHA256_EXPERIMENTOS](../SHA256_EXPERIMENTOS). Veja a [entrada de reprodução](../README.md).

# Artigo 01 · CNN centralizada × FedAvg na VM

**Concluído e conferido no Kubuntu em 25/11/2026 21:39:10 BRT, America/Belem.** Rodada na VM: **21:23:01–21:31:34 BRT**, cerca de **8 min 33 s** até finalizar os treinos, dentro do teto de 45 min. Não houve limite de tempo atingido nem etapa pendente da execução solicitada.

Pasta documental no Kubuntu:

```text
/home/willian/Projetos/secfednet/secfednet-local/artigo-01/execucoes/2026-11-25/vm-rodada-limitada-21-11-59/retorno_vm
```

Pasta completa na VM:

```text
/home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/2026-11-25/rodada-limitada-21-11-59
```

## Reprodução e integridade

VM confirmada por libvirt (UUID d7651c2c-2847-49d6-aeaf-db8c0406fef9), SSH hostname/usuário/MAC; IP 192.168.122.8, MAC 52:54:00:16:cd:d7. Quatro CPUs i3-10100, RAM visível ~7,25 GiB, ~2,9 GiB disponível no início, swap 4 GiB (~2 livres), disco ~31 GiB livres. Aplicativos existentes preservados. Kubuntu tem 8 CPUs lógicas; modelos usaram dois threads Torch/interop um, sequencialmente, nos dois ambientes.

Foram enviados **24 arquivos mínimos, 80.271 bytes comprimidos**: fontes, lock, contratos e referências. O ZIP existente foi reutilizado, SHA **`97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`**, conferido novamente no fim. Ambiente novo instalado **offline** pelo lock, `pip check` aprovado; Python 3.14.4, NumPy 2.3.5, PyTorch 2.12.1+cpu, Flower 1.32.0. O ambiente antigo não foi alterado.

`reproduzir.sh` executado com destino novo. Gate de **231 campos, tolerância zero, aprovado antes de iniciar a comparação**: índices/máscaras e contagens, pré-processamento, 12 matrizes derivadas, pesos, scores/métricas da quinta e recargas iguais ao Kubuntu. [Checks completos](tabelas/reproducao_checks.csv).

Os arquivos de checkpoint reproduzidos têm SHA diferente porque incluem o hash do manifesto de cada execução (tempo/pico variam). **Prova em cópia temporária:** trocar somente `configuracao.manifesto_sha256` pelo valor do Kubuntu reproduziu exatamente os dois SHA originais, sem alterar pesos ou arquivos históricos. [Prova](logs/prova_checkpoints_apos_execucao.log). Não houve divergência numérica a investigar.

| Reprodução | Medida | Kubuntu | VM |
| --- | --- | ---: | ---: |
| baseline | tempo_treino_s | 1.570 | 1.506 |
| baseline | tempo_total_s | 7.418 | 6.372 |
| baseline | pico_rss_kib | 861564.000 | 863988.000 |
| fedavg_integracao | tempo_treino_s | 9.755 | 9.556 |
| fedavg_integracao | tempo_total_s | 14.522 | 14.164 |
| fedavg_integracao | pico_rss_kib | 1159812.000 | 1163052.000 |
| preparo_candidato | tempo_s | 112.046 | 109.534 |
| preparo_candidato | pico_rss_kib | 3452216.000 | 3383548.000 |

Tempos/pico são medidas de execução, sensíveis a carga, cache e virtualização; não se atribui uma causa isolada nem uma vantagem de velocidade. Versões numéricas foram iguais; recursos disponíveis diferem. [Tabela com deltas](tabelas/reproducao_tempo_ambiente.csv) · [conferência final da VM](logs/verificacao_final_vm.log).

## Protocolo pareado fixado antes dos treinos

BENIGN=0, ATTACK=1; rótulos nominais preservados. CNN-1D de 81 features idêntica; mesma normalização do treino (float64→float32), mesmos pesos iniciais por par e mesmas máscaras de quinta. Treino segunda–quarta: 1.184.424. Quinta principal: 288.171 BENIGN/71.907 ATTACK; sensibilidade: 256.522/71.907. **Sexta somente para manifesto, qualidade e interseções: sem previsões ou métricas de desempenho.**

Seeds **23, 41, 89**, partições **2305, 4105, 8905**, cinco clientes Dirichlet α=0,5, atribuição completa uma vez. Cinco épocas centrais versus cinco rodadas FedAvg, uma época local/rodada, participação integral. Adam lr=0,001, betas=(0,9;0,999), eps=1e-8, sem weight decay, lote 512. Reinício Adam por época central e por cliente/rodada federada, conforme configuração fixada. Embaralhamento global central e local federado; os minibatches não são idênticos, mas tamanho/seeds/política são registrados. **Limiar 0,5, sem calibração**.

| Seed | Método | Exposições | Passos Adam | Treino s | Pico RSS KiB |
| --- | --- | ---: | ---: | ---: | ---: |
| 23 | central | 5922120 | 11570 | 48.391 | 914112 |
| 23 | fedavg | 5922120 | 11580 | 46.268 | 1164692 |
| 41 | central | 5922120 | 11570 | 48.160 | 913708 |
| 41 | fedavg | 5922120 | 11580 | 47.863 | 1164468 |
| 89 | central | 5922120 | 11570 | 49.034 | 913668 |
| 89 | fedavg | 5922120 | 11575 | 48.331 | 1165328 |

Inicialização, partição e máscaras pareadas tiveram os mesmos hashes. **Exposições iguais; FedAvg tem 10/10/5 passos adicionais** nas seeds 23/41/89 pelas caudas dos lotes. Os estados Adam são segregados por cliente, portanto trajetórias não são equivalentes. Tempos não são benchmark de sistemas. [Orçamento e hashes](tabelas/orcamento_por_seed.csv).

## Desempenho exploratório na quinta, por seed

AP é **average precision** (soma Δrecall×precision, empates agrupados; positivo ATTACK; sem trapézios). Matriz na ordem real/previsto BENIGN, ATTACK. Precisão também está no CSV completo.

| Seed | Método | Máscara | AP | Macro-F1 | Recall ATTACK | FPR | [[VN,FP],[FN,VP]] |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 23 | central | principal | 0,673941 | 0,513220 | 7,0118% | 0,0663% | [[287980,191],[66865,5042]] |
| 23 | central | sensibilidade_raw64 | 0,683973 | 0,507527 | 7,0118% | 0,0745% | [[256331,191],[66865,5042]] |
| 23 | fedavg | principal | 0,704860 | 0,535288 | 9,4636% | 0,0746% | [[287956,215],[65102,6805]] |
| 23 | fedavg | sensibilidade_raw64 | 0,709913 | 0,529710 | 9,4636% | 0,0838% | [[256307,215],[65102,6805]] |
| 41 | central | principal | 0,552378 | 0,443488 | 0,0292% | 0,5452% | [[286600,1571],[71886,21]] |
| 41 | central | sensibilidade_raw64 | 0,565498 | 0,437325 | 0,0292% | 0,6124% | [[254951,1571],[71886,21]] |
| 41 | fedavg | principal | 0,548657 | 0,463021 | 1,7995% | 0,0264% | [[288095,76],[70613,1294]] |
| 41 | fedavg | sensibilidade_raw64 | 0,556468 | 0,457094 | 1,7995% | 0,0296% | [[256446,76],[70613,1294]] |
| 89 | central | principal | 0,490472 | 0,490361 | 4,8132% | 0,5920% | [[286465,1706],[68446,3461]] |
| 89 | central | sensibilidade_raw64 | 0,507183 | 0,484407 | 4,8132% | 0,6651% | [[254816,1706],[68446,3461]] |
| 89 | fedavg | principal | 0,461353 | 0,451133 | 0,6369% | 0,0177% | [[288120,51],[71449,458]] |
| 89 | fedavg | sensibilidade_raw64 | 0,469008 | 0,445155 | 0,6369% | 0,0199% | [[256471,51],[71449,458]] |

### Variação entre as três seeds

Média ± desvio amostral (ddof=1), sem intervalo de confiança ou teste de significância.

| Método | Máscara | AP | Macro-F1 | Recall ATTACK | FPR |
| --- | --- | --- | --- | --- | --- |
| central | principal | 0,572264 ± 0,093337 | 0,482356 ± 0,035548 | 3,9514% ± 3,5702% | 0,4012% ± 0,2910% |
| central | sensibilidade_raw64 | 0,585552 ± 0,090085 | 0,476420 ± 0,035776 | 3,9514% ± 3,5702% | 0,4506% ± 0,3268% |
| fedavg | principal | 0,571623 ± 0,123367 | 0,483147 ± 0,045545 | 3,9667% ± 4,7958% | 0,0396% ± 0,0307% |
| fedavg | sensibilidade_raw64 | 0,578463 ± 0,121949 | 0,477320 ± 0,045762 | 3,9667% ± 4,7958% | 0,0444% ± 0,0344% |

DP nas mesmas unidades, em pontos percentuais nas colunas percentuais. [Mínimo, máximo, precisão e demais estatísticas](tabelas/variacao_entre_seeds.csv).

**Leitura para a escrita:** AP e macro-F1 médias próximas, recall baixo (~4% no principal) e variação relevante entre seeds. A ordenação por AP muda por seed. Estes resultados não sustentam conclusão de superioridade de um método. O limiar fixo não foi ajustado para otimizar recall/FPR.

### Suporte e recall por tipo nominal, quinta principal

Média e intervalo mínimo–máximo entre seeds; números por seed e sensibilidade no CSV. BENIGN corresponde a especificidade; tipos ausentes têm suporte 0/recall NA.

| Tipo | Suporte | Central: média [mín–máx] | FedAvg: média [mín–máx] |
| --- | ---: | --- | --- |
| BENIGN | 288171 | 99,5988% [99,4080%–99,9337%] | 99,9604% [99,9254%–99,9823%] |
| Infiltration | 36 | 0,9259% [0,0000%–2,7778%] | 0,0000% [0,0000%–0,0000%] |
| Infiltration - Portscan | 71767 | 3,9582% [0,0279%–7,0255%] | 3,9735% [0,6382%–9,4821%] |
| Web Attack - Brute Force | 73 | 0,0000% [0,0000%–0,0000%] | 0,9132% [0,0000%–2,7397%] |
| Web Attack - SQL Injection | 13 | 2,5641% [0,0000%–7,6923%] | 0,0000% [0,0000%–0,0000%] |
| Web Attack - XSS | 18 | 0,0000% [0,0000%–0,0000%] | 0,0000% [0,0000%–0,0000%] |

[Todos os 192 registros nominais](tabelas/recall_por_tipo.csv). A quinta concentra 99,805% dos positivos em Infiltration - Portscan; tipos raros têm suporte de apenas 13–73. Seeds variam inicialização, minibatches e partição conjuntamente. Sensibilidade bruta mantém **44/46/9 chaves compartilhadas após transformação float32** nos três pares. Protocolo permanece candidato, sem expurgo adicional nem métricas na sexta. A revisão do protocolo deve anteceder qualquer avaliação de sexta.

## Execução persistente, retorno e estado final

Supervisor `nohup` + nova sessão + `timeout 2700s`; reserva interna para finalizar. Sessões/filhos sem TTY foram confirmados; o terminal pode ser fechado. **Job encerrado**, sem supervisor de treino ativo. Acompanhamento histórico:

```bash
ssh williian@192.168.122.8 'cat /home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/2026-11-25/rodada-limitada-21-11-59/STATUS.json'
ssh williian@192.168.122.8 'tail -F /home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/2026-11-25/rodada-limitada-21-11-59/execucao.log'
```

Foram recebidos **27 documentos / 141.115 bytes**, todos SHA-256 conferidos: relatório original, cinco tabelas, logs e manifesto. Modelos, dados, máscaras e scores permanecem na VM. O log da prova final veio por consulta somente leitura, sem previsão nem alteração de checkpoint. Esta consolidação e a tabela de tempos foram elaboradas no Kubuntu, preservando o [relatório original da VM](RELATORIO_2026-11-25_21-31-34_BRT_VM_CNN_5x5.md).

[Manifesto da execução/acervo na VM](manifesto_execucao.json) · [hashes da cópia documental original](../historicos/vm_SHA256_RETORNO_VM) · [hashes da entrega local consolidada](../historicos/vm_SHA256_ENTREGA_LOCAL). O manifesto VM contém hashes de artefatos que ficam na VM; o manifesto local cobre apenas arquivos presentes aqui.

Git no Kubuntu: `integracao/artigo-01`, HEAD `0b38f255af6f22e4642c584c0f0e09b15ef9263e`, stage vazio, duas modificações e quatro caminhos não rastreados preexistentes preservados. Na VM: mesmo HEAD, destacado e limpo antes/depois, 90 arquivos versionados preservados. Nenhum stage, commit, push, PR, alteração de visibilidade ou de configuração global. ZIP e split históricos intactos. INDEX/STATUS locais complementados. Instruções/skill: AGENTS.md e secfednet-validar-experimento; nenhum subagente.

Para reproduzir, transferir `fonte/`, `controle/` e referências da pasta local desta missão a **novo destino VM**, reconstruir o lock e iniciar o supervisor com limite externo de 2700 s; os comandos efetivamente executados estão no manifesto. Fontes locais: `/home/willian/Projetos/secfednet/secfednet-local/artigo-01/execucoes/2026-11-25/vm-rodada-limitada-21-11-59`. Não reutilizar saídas existentes. Concluído: reprodução, três pares CNN, variação e conferência documental. Pendente: revisão do candidato e eventual avaliação futura da sexta, não autorizada nesta rodada.
