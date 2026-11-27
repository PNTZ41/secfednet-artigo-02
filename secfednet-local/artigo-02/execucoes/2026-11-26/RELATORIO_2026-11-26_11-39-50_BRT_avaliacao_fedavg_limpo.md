# Artigo 02 · Proposta de avaliação do FedAvg limpo em BENIGN × DDoS

26/11/2026, 11:39:50, Belém (UTC−03). Protocolo proposto para revisão. O objetivo é estimar recall DDoS e taxa de falsos positivos em capturas independentes, com o limiar definido em um conjunto de calibração separado.

## Evidência disponível e referência histórica

A auditoria de capturas mais recente encontrada no checkout está registrada no Artigo 01. Ela orienta esta nova frente do Artigo 02. No inventário corrigido do CICIDS2017, segunda a quinta têm zero DDoS e a sexta contém 95.144 DDoS e 288.544 BENIGN. A sexta está reservada para teste. A versão de 78 atributos documentada por Gabriel é outra exportação do cenário de sexta. O acervo consultado ainda não identifica capturas suficientes para ajuste, calibração e avaliação independentes. [Auditoria de capturas](../../../artigo-01/execucoes/2026-11-26/RELATORIO_2026-11-26_11-34-25_BRT_capturas_dose_bsr.md) · [Inventário local](../../../../docs/artigo-01/expansao-2026-11-25/fonte/inventario_cinco_capturas.json).

O FedAvg-SGD histórico da rodada 20, seed de modelo 23 e partição 2305, foi medido em **validação interna da captura de sexta**. Essa partição de 50.815 fluxos (40.776 BENIGN e 10.039 DDoS) serviu tanto para escolher o limiar quanto para reportar o desempenho. O teste cronológico global ficou fora dessa execução. [Descrição do ensaio](../../../artigo-01/cnn-scaffold/README_20.md) · [Resultados da rodada 20](../../../artigo-01/cnn-scaffold/ensaio-20-rodadas/execucao/comparacoes.json).

| Limiar | VN | FP | FN | VP | FPR | Recall DDoS |
|---:|---:|---:|---:|---:|---:|---:|
| 0,365106 (ajustado na validação interna) | 40.370 | 406 | 84 | 9.955 | 0,996% | 99,163% |
| 0,5 | 40.772 | 4 | 8.771 | 1.268 | 0,00981% | 12,631% |

A auditoria histórica registrou disjunção entre ajuste e validação por grupo e vetor float32. Os dois conjuntos ainda pertencem à mesma captura. A rodada 20 é uma referência de configuração e desempenho interno. A proposta prevê novos pesos, normalização e limiar obtidos exclusivamente nas partições autorizadas do novo estudo. [Auditoria da partição](../../../artigo-01/cnn-validacao/particao/auditoria.json).

## Partições e critérios de aceite

O protocolo separa três funções. **Ajuste** treina a CNN e estima a normalização. **Calibração** escolhe somente o limiar para um checkpoint já fixado. **Avaliação independente** mede o desempenho com checkpoint, normalização e limiar congelados. Os manifestos de desenvolvimento e avaliação devem excluir a sexta reservada e qualquer reexportação derivada dela. A eventual avaliação final nessa reserva exige protocolo previamente congelado.

| Critério | Evidência verificável de aceite |
|---|---|
| Campanhas | Para sustentar independência entre campanhas, atribuir cada campanha inteira a uma única partição. Verificar interseção vazia de IDs de campanha entre pares de partições e documentar origem, ambiente, janela de coleta e proveniência. Distinguir nova coleta de reprocessamento, recorte ou cópia. |
| Sessões | Se a separação disponível for por sessão, atribuir cada sessão inteira a uma única partição. Verificar interseção vazia dos IDs de sessão e ausência de fluxo atravessando fronteiras. Documentar os limites temporais e a regra de formação de sessão, incluindo fuso e incerteza dos relógios. Se houver campanha compartilhada, limitar a conclusão à independência entre sessões dessa campanha. |
| Eventos e vetores | Conferir hashes de arquivos e IDs originais de fluxo. Onde necessário, cruzar quíntupla bidirecional e intervalo do fluxo com a regra de tempo congelada. Exigir zero eventos repetidos entre partições após resolver as coincidências. Auditar também vetores brutos, vetores normalizados em float64 e entradas finais em float32. Registrar chaves, linhas afetadas e conflitos BENIGN/DDoS. Adotar, como proposta, a exclusão das cópias coincidentes nos conjuntos posteriores (ajuste → calibração → avaliação), sob regra congelada antes de consultar scores. Coincidência numérica isolada e recorrência da quíntupla são diagnósticos separados da identidade de evento. |
| Contrato de entrada | Verificar 81 colunas numéricas finitas, com grafia e ordem iguais a `ordem_features` do contrato JSON após o mapeamento. Documentar para cada coluna a definição, unidade, sentido ida/volta, versão do extrator e tratamento de ausência. Exigir evidência de equivalência para cada conversão. Manter IP, timestamp, identificadores e rótulos no manifesto, fora do vetor do modelo. Padronizar em float64 com média e desvio populacional do ajuste (escala zero vira 1) e converter para float32. Conferir finitude depois da conversão. |
| Suporte | Exigir BENIGN e DDoS em ajuste, calibração e avaliação após limpeza. Publicar contagens por classe, partição, sessão/campanha e cliente de ajuste. Registrar partição e seed, presença de ambas as classes no conjunto agregado e clientes com suporte zero em alguma classe. Contabilizar à parte rótulos excluídos e conflitos. Exigir denominadores positivos para FPR e recall em cada estrato reportado, ou registrar a métrica como não estimável. |

A ausência de coincidências não basta para justificar generalização a outras campanhas. Para qualificar a amostra, publicar o número de sessões e campanhas independentes por classe. Antes de ler scores, fixar o número mínimo de unidades independentes e a precisão desejada para recall e FPR, considerando a dependência entre fluxos da mesma sessão. A calibração precisa de pelo menos 100 BENIGN para que um FP represente no máximo 1 ponto percentual. Esse é um requisito de resolução proposto, sem garantia de precisão. [Contrato JSON](../../../../integracao/artigo-01/contrato-cnn/contrato.json) · [Descrição da entrada](../../../../integracao/artigo-01/contrato-cnn/CONTRATO.md) · [Definições de sobreposição](../../../../docs/artigo-01/expansao-2026-11-25/METODO_AUDITORIA.md).

## Procedimento de avaliação proposto

1. Congelar os manifestos e hashes de ajuste, calibração e avaliação, a identidade dos clientes e as seeds. Fixar o orçamento de treino e a rodada 20 antes de consultar os resultados. Como ponto de partida, usar a configuração FedAvg-SGD histórica com cinco clientes e participação integral. Registrar qualquer diferença de partição ou configuração necessária para as novas capturas. [Configuração da referência](../../../artigo-01/cnn-scaffold/protocolo_20.json).
2. Treinar no ajuste e congelar o checkpoint e o normalizador. Gerar scores somente para calibração nessa etapa. Com decisão DDoS para `score >= limiar`, selecionar o candidato de maior recall DDoS sob FPR empírica ≤ 1%, com desempate por menor número de FP e, a seguir, maior limiar. Varrer os scores distintos sem dividir empates e incluir a opção acima do maior score (nenhum positivo). Se apenas soluções sem detecções forem viáveis, registrar o resultado degenerado. Salvar a regra, o limiar, as contagens, o hash da máscara de calibração e a identificação do checkpoint por seed.
3. Aplicar o limiar congelado à avaliação independente. Publicar matriz real×previsto, numeradores e denominadores de recall e FPR, precisão DDoS, macro-F1 e average precision. Apresentar resultados por sessão ou campanha e agregados, com a regra de agregação declarada. Reportar a incerteza na unidade independente, quando houver suporte, e manter limiar 0,5 somente como referência secundária predefinida. A FPR de 1% é uma restrição da calibração. A FPR da avaliação é um resultado a medir.

## Metadados pendentes para confirmar viabilidade

- **Origem e acesso:** arquivos ou manifestos verificáveis, identificação da coleta, versão, hashes e licença ou condições de uso. Vincular cada exportação à captura bruta e à campanha de origem.
- **Sessões e eventos:** identificadores de campanha, sessão e fluxo, início/fim, fuso, relógio, quíntupla e regra de agrupamento. Comprovar o vínculo entre reexportações, quando houver, e a exclusão dos derivados da sexta.
- **Esquema:** dicionário dos 81 atributos, ordem, unidade, algoritmo e versão do extrator, direção dos fluxos e política de conversão ou de ausência. Incluir evidência que permita testar equivalência em vetores de referência.
- **Rótulos e suporte:** origem do rótulo e distinção entre DDoS, outras classes e casos ambíguos. Contagens antes e depois dos filtros, por classe, sessão, campanha, partição e cliente. Registrar exclusões e conflitos para verificar se haverá resolução e precisão suficientes.
- **Manifestos congelados:** relação fluxo → partição → cliente de ajuste, hashes, política de deduplicação e resultados dos cruzamentos. Fixar o mínimo amostral e o método de incerteza após receber o inventário e antes de gerar scores.

O próximo passo é obter esse inventário e aplicar os critérios de aceite em uma auditoria de dados, antes de planejar qualquer execução do FedAvg independente.

## Registro desta missão

Branch inicial/final `integracao/artigo-01`, HEAD `4cc2727`. Estado visível inicial/final: índice rastreado do Artigo 01 já modificado e `.idea/` já não rastreada. A nova pasta ignorada `secfednet-local/artigo-02/` contém este relatório, `INDEX.md` e `STATUS.md`. A mudança foi documental. Nenhum treino, download ou inferência foi executado. Instrução aplicável em `AGENTS.md`. `.agents/` e `.codex/` vazios, sem outros caminhos de instruções ou skills locais no checkout.

Foram usados `git status`, `git rev-parse`, `rg`, `ls`, `cat`, `head`, `tail`, `sed` e `TZ=America/Belem date`. A conferência documental pode ser reproduzida da raiz com os comandos abaixo. Foram conferidos os vínculos relativos do relatório, a presença dos registros no índice e no status e o estado do Git.

```sh
cat secfednet-local/artigo-01/execucoes/2026-11-26/RELATORIO_2026-11-26_11-34-25_BRT_capturas_dose_bsr.md
head -50 secfednet-local/artigo-01/cnn-scaffold/ensaio-20-rodadas/execucao/comparacoes.json
cat integracao/artigo-01/contrato-cnn/contrato.json
git --no-optional-locks status --short --branch
```
