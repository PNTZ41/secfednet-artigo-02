# Artigo 01 · fechamento da expansão experimental

Fonte dos resultados: execuções concluídas em25/11/2026, auditoria20:22:28, candidato20:46:58 e VM21:11:59, com treinos concluídos21:31:34 e conferência21:39:10 BRT. Este fechamento documental não reestima desempenho. [Entrada](README.md), [método](METODOLOGIA.md), [reprodução](REPRODUCAO.md), [acervo](ACERVO.json).

## Auditoria das cinco capturas

Split candidato BENIGN × ATTACK por captura: segunda–quarta / quinta / sexta. Attempted separado;81 features. ZIP corrigido dos autores SHA 97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883.

| Cenário | Treino | Validação | Teste reservado |
| --- | ---: | ---: | ---: |
| Não-Attempted antes da finitude | 1184428 | 360079 | 543490 |
| Principal: remove5 linhas não finitas | 1184424 | 360078 | 543490 |
| Sensibilidade: finitude + exclusão sequencial vetor bruto float64 | 1184424 | 328429 | 429801 |

Cinco linhas BENIGN/dez células não finitas; nenhum vazio/inválido adicional. [Qualidade por feature](fonte/auditoria_referencia/qualidade_por_feature.csv). As referências da auditoria antecedem a remoção dessas cinco linhas; o candidato reconcilia as diferenças explicitamente.

| Par original | Chaves de vetor bruto compartilhadas | Linhas no lado anterior | Linhas no posterior |
| --- | ---: | ---: | ---: |
| Treino × validação | 19965 | 62395 | 31649 |
| Treino × teste | 20437 | 64403 | 33221 |
| Validação × teste | 10728 | 34882 | 96417 |

IDs inteiros são locais a cada CSV. Nenhuma coincidência de id escopado nem da quíntupla com timestamp. Grupos bidirecionais recorrentes:66.350/80.454/38.175 chaves; são recorrência de conexão, sem prova de duplicação do mesmo evento. Excluir grupos zeraria suporte de três ataques Web na validação; permanece diagnóstico. Pela exclusão bruta, Portscan na sexta cai159.066→82.737 (~48%); não é resultado de desempenho. [Simulações por tipo](fonte/auditoria_referencia/simulacoes_por_classe.csv).

Conflitos binários por vetor: treino×validação0; treino×teste1 chave; validação×teste13. Os conflitos nominais são maiores (110 chaves na última comparação), especialmente Infiltration-Portscan/Portscan. A fonte não foi relabelada. [Conflitos e multiplicidades](fonte/auditoria_referencia/conflitos.csv). Na sensibilidade, vetores brutos cruzados são zero, mas após transformaçãofloat32 restam44/46/9 chaves; o protocolo ainda precisa decidir esse tratamento.

## Baseline e integração no Kubuntu

Somente quinta, limiar 0,5. Logística3 épocas versus CNN FedAvg1 rodada são verificações com arquiteturas/orçamentos distintos.

| Modelo/cenário principal | AP | Macro-F1 | Recall ATTACK | FPR | [[VN,FP],[FN,VP]] |
| --- | ---: | ---: | ---: | ---: | --- |
| Logística | 0,531693 | 0,530787 | 0,113800 | 0,037533 | [[277355,10816],[63724,8183]] |
| CNN FedAvg integração | 0,571785 | 0,493506 | 0,049161 | 0,000767 | [[287950,221],[68372,3535]] |

[Valores completos e sensibilidade](baseline-kubuntu/metricas_quinta.csv). Recargas CPU registradas; sem decisão comparativa a partir desta dupla.

## Reprodução e comparação pareada na VM

Reprodução antes de comparar:231 checks/tolerância zero aprovados para índices, contagens, normalização,12 matrizes, pesos, scores, métricas e recargas. Diferença de SHA serializado explicada somente pelo hash de manifesto de cada execução (tempo/RSS): substituição temporária desse campo reproduziu ambos os SHA Kubuntu. Ambiente Python3.14.4/NumPy2.3.5/Torch2.12.1+cpu/Flower1.32.0; instalação pelo lock offline; treinos sequenciais com2 threads.

CNN centralizada5 épocas versus FedAvg5 rodadas/1 época local,5 clientesα=0,5. Seeds 23/41/89, pesos/partição/máscaras pareados, Adam lr0,001/lote 512, limiar 0,5. Mesmo número de exposições (5.922.120),11.570 passos centrais versus11.580/11.580/11.575 federados. Ver [orçamento](vm/tabelas/orcamento_por_seed.csv). A execução respeitou45 min (~8 min 33 s até finalização dos treinos).

| Método, quinta principal | AP média ± DP | Macro-F1 média ± DP | Recall ATTACK média ± DP | FPR média ± DP |
| --- | --- | --- | --- | --- |
| Centralizada | 0,572264 ± 0,093337 | 0,482356 ± 0,035548 | 3,9514% ± 3,5702 pp | 0,4012% ± 0,2910 pp |
| FedAvg | 0,571623 ± 0,123367 | 0,483147 ± 0,045545 | 3,9667% ± 4,7958 pp | 0,0396% ± 0,0307 pp |

DP amostral/ddof1. Suporte 288.171BENIGN/71.907ATTACK. [Resultados/matrizes por seed](vm/tabelas/resultados_por_seed.csv), [variação completa](vm/tabelas/variacao_entre_seeds.csv), [192 registros de suporte/recall nominal](vm/tabelas/recall_por_tipo.csv). Sensibilidade tem256.522BENIGN e os mesmos71.907ATTACK. Predições/máscaras compartilhadas, sem ajuste de limiar.

Recall baixo (~4%), variação relevante e ordenação por AP diferente por seed impedem concluir superioridade. Infiltration-Portscan concentra 99,805% dos ataques de quinta; tipos raros têm13–73 exemplos. Este recorte não estima generalização para todo ataque. Tempos/RSS diferem entre ambientes; não se atribui vantagem de velocidade nem causa isolada. [Diferenças de ambiente](vm/tabelas/reproducao_tempo_ambiente.csv).

## Entrega e pendências

Scripts/configurações, referências, tabelas, logs sanitizados e manifestos estão nesta seleção; grandes derivados e dados continuam no acervo. A [caracterização parcial de Gabriel](GABRIEL.md) é identificada separadamente. As46 evidências históricas de d27c89de permanecem herdadas, sem duplicação. O piloto históricoBENIGN × DDoS, seu teste e seu pacote CNN foram preservados.

Os links deste novo relatório são caminhos reais: [resultado da auditoria](fonte/auditoria_referencia/resultado.json), [cruzamentos](fonte/auditoria_referencia/cruzamentos.csv), [conflitos](fonte/auditoria_referencia/conflitos.csv), [pares nominais](fonte/auditoria_referencia/pares_rotulos_conflitantes.csv), [linhas por classe](fonte/auditoria_referencia/linhas_afetadas_por_classe.csv), [chaves](fonte/auditoria_referencia/chaves_por_conjunto.csv), [simulações](fonte/auditoria_referencia/simulacoes_por_classe.csv), [qualidade](fonte/auditoria_referencia/qualidade_por_feature.csv) e [método](METODO_AUDITORIA.md). Substituem as nove expressões literais de link do relatório histórico; o original permanece no acervo.

Protocolo candidato, sem congelamento final. Pendente: aprovar política de colisões/ambiguidade e desenho de cobertura por captura; revisar antes de qualquer desempenho na sexta. Avaliação de sexta, comparação ampliada, push, PR e merge não são parte deste fechamento. [Verificações da seleção](VERIFICACOES.md).
