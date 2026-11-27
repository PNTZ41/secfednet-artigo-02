# Commit local dos relatórios no SecFedNet

27/11/2026, 10h19, Belém. A pedido do responsável, o repositório principal em `/home/kali/PycharmProjects/SecFedNet` recebeu o índice e os dois relatórios que já estavam publicados no repositório do Artigo 02. O commit local é `190603c40e2bc5e789ca723c9e1366fc1a125a44` na branch `integracao/artigo-01`.

## Arquivos e resultado

O commit contém somente os três arquivos em `docs/artigo-02/relatorios/`. O índice aponta para os dois relatórios. A subárvore tem o identificador Git `32eee7c87b3dbbe659f799a312774ecb65645825`, igual ao da árvore publicada no commit `d5a9364`. [Índice no repositório principal](../../../../docs/artigo-02/relatorios/README.md)

A branch começou em `4cc2727` alinhada com a referência local de `origin/integracao/artigo-01` e terminou um commit à frente dela. O índice de trabalho em `secfednet-local/artigo-01/INDEX.md` já apresentava mudanças e `.idea/` já aparecia como não rastreada. Ambos ficaram fora do commit. O índice rastreado nesse caminho integra o manifesto histórico `SHA256_ENTREGA`, e seu conteúdo no commit continuou com o hash registrado. Foram atualizados localmente o índice de trabalho, o status do Artigo 01 e este relatório. A operação foi local.

## Conferência

Usei `git status`, `git rev-parse`, `git remote -v`, `git check-ignore`, `git diff`, `rg`, `ls`, `cat` e a data em `America/Belem` para inspecionar a origem. Copiei os documentos com `mkdir -p` e `cp`, conferi a igualdade com `cmp` e verifiquei o hash histórico do índice com `git show` e `sha256sum`. O primeiro `git add` encontrou `.git/` em modo somente leitura. A execução aprovada gravou os três caminhos com `git add` e `git commit`, após `git diff --cached --check`. A revisão final usou `git show --stat`, `git diff --check` e a igualdade dos identificadores das árvores.

```sh
git show --stat --oneline 190603c
git rev-parse 190603c:docs/artigo-02/relatorios
git -C secfednet-local/secfednet-relatorios rev-parse 'origin/main^{tree}'
```

A instrução aplicável foi `AGENTS.md` na raiz. As pastas locais `.agents/` e `.codex/` estavam vazias. O pedido de commit local está concluído.
