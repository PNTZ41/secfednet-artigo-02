# Versionamento local do acervo do SecFedNet

27/11/2026, 10h27, Belém. O pedido abrangeu `docs/`, `integracao/`, `secfednet-local/` e `SecFedNet_CICIDS2017_entrega/`. O commit «Versiona registros e scripts da auditoria do SecFedNet» reúne as alterações pendentes em `secfednet-local/`. Os outros três diretórios já estavam versionados e sem alterações pendentes.

## Conteúdo

- Relatórios, evidências documentais, índices e arquivos de status dos Artigos 01 e 02.
- Scripts da retomada limpa, exportação das partições internas e auditoria defensiva da agregação.
- JSON de auditoria, pesos e pontuações da rodada 10 reproduzida. As duas saídas foram novamente comparadas com as referências da VM pelos hashes registrados.
- Índice de execuções do Artigo 01 com os registros que estavam acrescentados ao índice histórico de distribuição. O índice histórico voltou ao conteúdo registrado em `SHA256_ENTREGA`. [Índice de execuções](../INDEX.md)

Os ambientes `.venv*`, o Python de referência, o NPZ de ajuste e validação interna e o repositório aninhado `secfednet-relatorios/` permanecem no acervo local. Os três Markdown desse repositório já estão versionados em `docs/artigo-02/relatorios/`. A pasta `.idea/` estava fora do escopo.

## Git e verificação

A branch `integracao/artigo-01` estava em `190603c`, um commit à frente da referência local do upstream. O índice histórico tinha apenas a seção adicional de registros e `.idea/` já aparecia como não rastreada. A seção foi transferida para `execucoes/INDEX.md`, com os links ajustados à nova pasta. A branch recebeu um novo commit local, ficando dois commits à frente da referência local do upstream.

Foram usados `git status`, `git ls-files`, `git diff`, `git log`, `git show`, `rg`, `ls`, `du`, `stat`, Python para conferir os índices e a sintaxe dos scripts, `sha256sum` e a data em `America/Belem`. A inclusão dos arquivos sob a regra de exclusão geral foi explícita em `git add -f`, com revisão por `git diff --cached --check` e `git diff --cached --stat` antes do commit. Os comandos a seguir conferem a integridade da entrega histórica e listam o conteúdo do commit.

```sh
sha256sum -c SHA256_ENTREGA --quiet
git log -1 --oneline -- secfednet-local/artigo-01/execucoes/2026-11-27/RELATORIO_2026-11-27_10-27-09_BRT_commit_acervo_secfednet.md
git show --stat --oneline HEAD
```

A instrução aplicável foi `AGENTS.md` na raiz. As pastas `.agents/` e `.codex/` estavam vazias. A verificação foi documental e de integridade. O commit local encerra o pedido.
