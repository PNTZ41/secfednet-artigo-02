# Auditoria do split candidato por captura

Sem normalização, treino, gravação de índices ou exclusão dos dados. Conjuntos de referência não-Attempted: treino segunda–quarta 1.184.428; validação quinta 360.079; teste sexta 543.490. Alvo binário desta expansão: BENIGN versus ATTACK (qualquer outro rótulo nominal não-Attempted), diferente do piloto BENIGN/DDoS.

## Leitura e comparação

As 81 features são selecionadas excluindo os oito metadados (`id`, `Flow ID`, IPs/portas, protocolo, timestamp) e `Label`/`Attempted Category`. Cabeçalhos devem ter 91 nomes distintos e a mesma ordem nos cinco arquivos, no inventário anterior e no contrato da CNN. Os nomes das features não são normalizados. SHA do ZIP e de cada membro CSV conferidos com as referências.

Attempted segue o piloto: categoria diferente de `-1` OU sufixo ` - Attempted`, sem reinterpretar tentativas como ataques concluídos. Todos os demais rótulos nominais são mantidos nesta expansão. Datas/timestamps usam a convenção original de UTC sem offset; não se afirma que o fuso foi verificado externamente.

Qualidade das features, somente na população não-Attempted: vazio é texto vazio após strip; inválido é não conversível por `float`; não finito é NaN/+Inf/-Inf após conversão, inclusive overflow. Categorias mutuamente exclusivas por célula. Negativos finitos, incluindo sentinelas como -1, não são chamados inválidos sem regra de domínio. Percentuais usam as linhas do conjunto/classe antes de exclusões. São produzidas contagens por feature e por dia/conjunto e contagens de linhas com um ou mais problemas. Não há imputação.

| Chave | Semântica e limites |
| --- | --- |
| `id_local_escopado` | (`arquivo`, `id` inteiro). IDs sequenciais locais não são cruzados como se fossem globais. A contagem de id/distintos/min/max/sequencialidade é feita em todas as linhas, incluindo Attempted. |
| `flow_id_direcional` | `Flow ID` interpretado como IP origem, IP destino, porta origem inteira, porta destino inteira, protocolo inteiro. Confere consistência com os metadados em direção direta ou reversa. Canonicaliza a representação decimal das portas/protocolo, preserva a direção. Não inclui timestamp e pode representar muitas ocorrências da mesma quíntupla. |
| `grupo_bidirecional` | Mesma chave do piloto: `(int(protocolo), *sorted(((IP_origem_literal, int(porta_origem)), (IP_destino_literal, int(porta_destino)))))`. Ordenação lexicográfica das strings IP e numérica das portas. Não contém data, timestamp ou rótulo. Recorrência de conexão, não prova do mesmo fluxo. |
| `vetor_float64` | Bytes dos 81 números convertidos para IEEE754 float64 little-endian, na ordem literal. Sem arredondamento; -0.0/+0.0 são iguais. Rótulos, timestamps e identificadores não entram. Só há chave quando todas as 81 medidas são finitas/válidas. |
| `flow_id_timestamp` | Âncora adicional: quíntupla direcional mais timestamp exato em microssegundos. Mede possível coincidência de evento, sem afirmar unicidade forense. Não é uma feature nem critério de exclusão simulado. |

As chaves de vetor são comparadas por bytes completos, não só por digest. Dicionários codificam as chaves em memória com IDs comuns às cinco capturas; colisões internas do hash de Python são resolvidas pela igualdade completa. Nenhum vetor real, índice ou máscara de simulação é exportado.

Metadados ausentes/inválidos geram diagnóstico e ausência de chave no critério afetado. Além do piloto, a auditoria valida sintaxe IP, faixa das portas 0..65535 e protocolo 0..255; não exclui linhas por esses testes. Timestamp inválido exclui só a âncora de evento. Valores de features inválidos ficam fora só da igualdade de vetor; permanecem nas contagens e nos critérios de metadados. Uma simulação separada mostra a exclusão por qualidade numérica em todos os conjuntos.

## Cruzamentos e conflitos

Três pares originais independentes: treino × validação; treino × teste; validação × teste. Para cada chave: número de valores distintos comuns; linhas afetadas em cada lado (cada linha contada uma vez); percentuais e distribuição por classe. Repetições dentro de um lado são preservadas e contadas separadamente.

Conflito nominal/binário significa **existir pelo menos um par de linhas da mesma chave, uma de cada lado, com rótulos diferentes**. Não é diferença entre conjuntos de classes. São informados: chaves com conflito, linhas nas chaves conflitantes, linhas que têm pelo menos uma contraparte com rótulo oposto e número de pares de linhas opostos. Este último pondera multiplicidades e pode ser muito maior que o número de exemplos; não deve ser interpretado como quantidade de registros duplicados. Para quíntuplas e grupos, a discordância pode ser legítima entre eventos diferentes; não prova erro de anotação.

## Simulações independentes

- `sem_exclusao`: referência original sem Attempted.
- `qualidade_numerica_todos_conjuntos`: simula excluir linhas com qualquer feature vazia, inválida ou não finita, em todos os conjuntos.
- `par_A_x_B_vetor_float64` e `par_A_x_B_grupo_bidirecional`: compara o par original e simula excluir somente as linhas de B com chave em A; outros conjuntos ficam intactos.
- `sequencial_vetor_float64` e `sequencial_grupo_bidirecional`: separadamente para cada critério, preserva treino, retira da validação chaves presentes no treino e retira do teste chaves presentes no treino OU na validação original. Como cada critério é uma relação de equivalência, a união das chaves anteriores originais é igual à união das anteriores retidas: as removidas já pertenciam ao treino. O script verifica disjunção final da simulação. Não combina grupo e vetor numa política única.

Linhas sem chave no critério não são consideradas iguais nem excluídas por ele. Não há deduplicação interna por iniciativa própria. A tabela de simulação traz contagem antes/depois, exclusão absoluta, fração da classe perdida e composição do conjunto antes/depois, em escalas nominal/binária. As marcações de perda ≥10%, ≥50%, suporte zerado e suporte final <100 são diagnósticos descritivos, não regras aprovadas de seleção.

Estas alternativas retiram exemplos dos conjuntos posteriores conforme solicitado. **Diferem do piloto cronológico de sexta**, que preservava teste e expurgava treino. O antigo split, suas 29 remoções adicionais e seus artefatos não são reaplicados a este novo candidato nem modificados. Não há padronização ajustada: esta auditoria trata medidas brutas em float64; possíveis coincidências após normalização/conversão float32 ainda precisariam de auditoria futura, somente após decidir o protocolo.
