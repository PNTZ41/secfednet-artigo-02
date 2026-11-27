# Erro do FedAvg limpo e condições para avaliação independente

**O recall de 99,163% da rodada 20 é um resultado de validação interna.** A referência BENIGN × DDoS usou os mesmos 40.776 fluxos BENIGN e 10.039 DDoS para selecionar o limiar e medir o desempenho. O efeito dessa escolha aparece nas contagens da mesma rodada.

| Limiar de decisão DDoS | BENIGN classificados como DDoS | DDoS classificados como BENIGN | Recall DDoS |
|---|---:|---:|---:|
| 0,365106, selecionado na validação | 406 | 84 | 99,163% |
| 0,5 | 4 | 8.771 | 12,631% |

## O que a expansão mediu

A expansão de cinco rodadas mede BENIGN × ATTACK. Na quinta-feira, com limiar 0,5 e os mesmos 71.907 positivos, o FedAvg classificou como BENIGN 65.102 ataques na seed 23, 70.613 na seed 41 e 71.449 na seed 89. Somar as três contagens repetiria fluxos. A captura tem 71.767 positivos de um único tipo, Infiltration - Portscan. Essas contagens descrevem o erro limpo nessa composição de tráfego. O desempenho sobre DDoS pertence ao ensaio da tabela anterior.

Na análise de sensibilidade da expansão, a exclusão de coincidências nos vetores brutos ainda deixou 44 chaves de entrada float32 compartilhadas entre treino e quinta, abrangendo 305 linhas de treino e 57 de quinta. Nessa comparação de sensibilidade, a auditoria encontrou zero conflitos de rótulo cruzados. Para interpretar uma coincidência, é preciso confrontar o vetor com a identidade e o intervalo temporal do fluxo. A política de exclusão deve ser definida antes da avaliação e acompanhada das contagens por classe que restarem.

## Capturas candidatas de 2018

Os cabeçalhos corrigidos de 20 e 21 de fevereiro contêm os 81 atributos na ordem esperada. A auditoria encontrou documentação da regra de cálculo para 55 atributos e verificações específicas pendentes em 26. Os prefixos lidos continham 12 e 10 linhas BENIGN, respectivamente. As contagens diárias abaixo provêm das saídas publicadas do notebook de rotulagem, com os casos *Attempted* excluídos dos positivos.

| Data | BENIGN publicados | DDoS publicados |
|---|---:|---:|
| 20/02/2018 | 5.764.497 | 290.125 |
| 21/02/2018 | 5.878.399 | 1.084.023 |

As duas datas compartilham infraestrutura. Para qualificar o checkpoint em outra captura, faltam duas evidências. A primeira é uma amostra dos mesmos pacotes processada pelas versões e configurações efetivas dos dois extratores. A comparação deve cobrir taxas quando a duração é zero, conversões inteiras e duração TCP acumulada. A segunda é um manifesto com origem, campanha, sessão, intervalo, fuso, identificador do fluxo e contagens pós-filtro de ambas as classes. Esses registros permitem distinguir nova coleta de reexportação e detectar eventos que atravessam as partições.

## Decisão metodológica pendente

O protocolo propõe atribuir cada campanha inteira a uma partição, ou limitar a conclusão às sessões quando a campanha for compartilhada. Antes de gerar pontuações, verificar interseções de IDs e de eventos, suporte por classe e hashes dos manifestos. O ajuste estima pesos e normalização. A calibração seleciona o limiar de maior recall sob FPR empírica de até 1%. A avaliação independente recebe o checkpoint, a normalização e o limiar congelados e reporta a matriz de confusão, recall e FPR por sessão ou campanha. A sexta-feira reservada do CICIDS2017 permanece destinada ao teste final.

O acervo original registra as matrizes da rodada 20 em `secfednet-local/artigo-01/cnn-scaffold/ensaio-20-rodadas/execucao/comparacoes.json`, os resultados da expansão em `docs/artigo-01/expansao-2026-11-25/vm/tabelas/` e o mapeamento coluna a coluna em `secfednet-local/artigo-02/execucoes/2026-11-26/RELATORIO_2026-11-26_11-56-51_BRT_compatibilidade_cicids2018.md`. As definições dos rótulos e o procedimento de correção estão documentados pelos autores. [Documentação do CSE-CIC-IDS2018 corrigido](https://intrusion-detection.distrinet-research.be/CNS2022/CSECICIDS2018.html)
