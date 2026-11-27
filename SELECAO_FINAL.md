# Seleção final para revisão local

Base: os 70 arquivos auditados, mantidos sem edição. O inventário em `cnn-validacao/PRIMEIRO_COMMIT.md` permanece como registro daquela seleção. O conjunto atual é definido por `LISTA_ARQUIVOS.txt` e `SHA256_ENTREGA`, na raiz desta cópia.

Acrescentados: README de entrada; README histórico de integração e seus seis artefatos/requirements; ficha e caracterizador originais de Gabriel; índice de distribuição; contrato CNN em Markdown/JSON, identidade e exemplos retirados do ZIP preservado; esta seleção e os arquivos de fechamento.

As três referências ausentes foram resolvidas nos caminhos originais: `integracao/artigo-01/README.md`, `SecFedNet_CICIDS2017_entrega/ficha_CICIDS2017.md` e `secfednet-local/artigo-01/INDEX.md`. O último é um índice curado deste conjunto; o índice cronológico original não foi substituído.

O ZIP da CNN é entregue separadamente em `../pacote-inferencia/secfednet-cnn1d-v1.zip`: código, checkpoint, contrato, exemplos, lock e manifesto próprios. Não faz parte do TAR de código. Os CSVs/ZIP de dataset, virtualenvs, cache e checkpoints gerados por novos treinos também ficam fora do TAR. Os dois recursos opcionais Codex permanecem fora desta seleção para consumidores.

Os manifestos históricos permanecem nos caminhos auditados e com o conteúdo original. Alguns apontam para acervo externo a este conjunto. Para verificar esta entrega, execute somente o novo `SHA256_ENTREGA`; ele cobre todos os arquivos entregues no TAR, exceto ele próprio. O `SHA256_DISTRIBUICAO`, um nível acima, cobre os arquivos reais da distribuição incluindo os dois pacotes e o manifesto interno.

Não houve stage, commit ou push. Esta seleção é uma cópia de revisão em pasta ignorada; qualquer inclusão futura no Git depende de autorização de Willian.
