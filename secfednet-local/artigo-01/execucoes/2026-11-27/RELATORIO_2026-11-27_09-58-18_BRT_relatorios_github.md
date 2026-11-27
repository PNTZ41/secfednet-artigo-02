# Relatórios do SecFedNet para publicação no GitHub

**Fechamento em 27/11/2026.** A publicação pública foi autorizada e conferida no destino indicado posteriormente, `PNTZ41/secfednet-artigo-02`. O registro abaixo descreve a preparação anterior ao envio. [Conferência final](RELATORIO_2026-11-27_10-07-59_BRT_publicacao_verificada.md)

27/11/2026, 09h58, Belém. O objetivo foi registrar os achados da reprodução e das auditorias em um repositório próprio. O commit local `21748a3b9baeb405b620878778409115fef93a78`, na branch `relatorios`, contém três arquivos Markdown. A publicação no GitHub está pendente.

## Entrega e conferências

- [Índice de leitura](../../../secfednet-relatorios/README.md).
- [Rodada 10 limpa e auditoria do servidor](../../../secfednet-relatorios/rodada-10-fedavg.md). Nesta missão, `cmp` confirmou novamente a igualdade byte a byte dos pesos e das pontuações com os arquivos da VM. O relatório traz os SHA-256, as contagens por classe, as seeds, as normas L2 e os comandos para repetir a comparação. As evidências sobre a execução vêm do [registro da retomada](RELATORIO_2026-11-27_08-49-40_BRT_retomada_10_reproduzida.md).
- [Erro limpo e avaliação independente](../../../secfednet-relatorios/avaliacao-independente.md). A síntese identifica os denominadores da quinta-feira na expansão, o uso da validação interna na escolha do limiar da rodada 20 e os insumos pendentes para verificar compatibilidade numérica e independência das capturas de 2018.

O repositório documental foi inicializado em `secfednet-local/secfednet-relatorios/`, com identidade local usando o endereço noreply da conta GitHub conectada. A inspeção da árvore do commit confirmou os três Markdown. O trabalho se limitou à síntese documental e à conferência dos arquivos de saída existentes. O conjunto reservado para teste ficou fora da missão.

## Estado do Git e publicação

O projeto de origem iniciou e encerrou a missão em `integracao/artigo-01`, HEAD `4cc2727`, com `secfednet-local/artigo-01/INDEX.md` modificado e `.idea/` não rastreada já no início. As edições na origem foram este registro, o índice e o status do Artigo 01. O novo repositório Git tem histórico próprio, branch `relatorios` e árvore de trabalho limpa após o commit.

O destino privado sugerido foi `PNTZ41/secfednet-relatorios`. O conector identificou a conta, mas devolveu HTTP 404 ao consultar esse nome. O conector disponível não expõe criação de repositórios. O executável `gh` está ausente e a tentativa de consulta direta por SSH recebeu `Permission denied (publickey)`. A URL do destino privado acessível ainda precisa ser confirmada. Depois disso, publicar os três documentos e conferir o conteúdo da branch remota.

## Comandos e instruções

Na origem, foram usados `git status --short --branch`, `git rev-parse HEAD`, `git remote -v`, `cat`, `rg`, `ls`, `cmp`, `sha256sum`, `TZ=America/Belem date` e `git diff --check`. Para o novo repositório, foram usados `git init -b relatorios`, `git config` local, `git add` dos três documentos, `git diff --cached --check`, `git commit`, `git ls-tree`, `git rev-parse` e `git status`. A disponibilidade do remoto foi consultada com o conector GitHub e com `git ls-remote`.

Para conferir o conteúdo do commit a partir da raiz do SecFedNet, execute:

```sh
git -C secfednet-local/secfednet-relatorios ls-tree -r --name-only 21748a3
git -C secfednet-local/secfednet-relatorios show --stat --oneline 21748a3
```

Instrução aplicável em `AGENTS.md` na raiz. Os diretórios locais `.agents/` e `.codex/` estavam vazios. A instrução de estilo consultada pertence à instalação do Codex em `~/.codex/plugins/cache/openai-curated-remote/write-like-me/0.1.1/skills/write-like-me/SKILL.md`.
