# Publicação verificada dos relatórios do SecFedNet

27/11/2026, 10h07, Belém. Os dois relatórios e o índice de leitura estão publicados na branch `main` de `PNTZ41/secfednet-artigo-02`. O responsável forneceu o destino SSH e autorizou expressamente a publicação dos três Markdown no repositório público. [Árvore publicada](https://github.com/PNTZ41/secfednet-artigo-02/tree/d5a936464277b74f3ff377661ef20213db3c4dd3)

## Arquivos e verificação

| Arquivo publicado | Objeto Git do conteúdo |
|---|---|
| `README.md` | `c6380d9a5a7a3704b7dfb82109ded2fb6958ca8e` |
| `avaliacao-independente.md` | `3280d0598531f9c0f9c2707ccaa712e0cc8f3e3c` |
| `rodada-10-fedavg.md` | `93c4b0dd7e613796c5059ab06ae910e2b4edad52` |

O commit local da branch `relatorios` é `21748a3b9baeb405b620878778409115fef93a78`. O GitHub recebeu primeiro o relatório da rodada 10 no commit `56e11a8f810ed58bc617dfa82146877dfc6a9ad2`, seguido do índice e do relatório de avaliação no commit `d5a936464277b74f3ff377661ef20213db3c4dd3`. O histórico de publicação explica os identificadores de commit distintos. Uma releitura por HTTPS confirmou a mesma árvore `32eee7c87b3dbbe659f799a312774ecb65645825` em ambas as pontas. A comparação dos três documentos retornou código zero.

## Registro e reprodução

Na origem, `git status --short --branch` mostrou `integracao/artigo-01` em `4cc2727`, com o índice do Artigo 01 já modificado e `.idea/` já não rastreada, no início e no final. No repositório documental, a branch local `relatorios` começou e terminou limpa. Foi configurado `origin` para o endereço SSH informado e registrada a referência local `origin/main` após a conferência. No Artigo 01, foram atualizados `INDEX.md`, `STATUS.md` e o [registro anterior](RELATORIO_2026-11-27_09-58-18_BRT_relatorios_github.md), com este novo relatório como fechamento.

Foram consultados `AGENTS.md`, `git status`, `git remote`, `git rev-parse`, `git log`, `git ls-tree`, `git cat-file`, `git show` e a data de Belém. As pastas de instruções locais `.agents/` e `.codex/` estavam vazias. Após `git remote add origin`, a consulta `git ls-remote --heads origin` falhou na autenticação por chave. O conector autenticado do GitHub consultou o repositório e as branches, criou o primeiro arquivo, os objetos e o segundo commit, e avançou a referência da branch. A conferência abaixo pode ser repetida a partir da raiz do projeto original.

```sh
set -e
repo=secfednet-local/secfednet-relatorios
git -C "$repo" fetch --no-tags https://github.com/PNTZ41/secfednet-artigo-02.git refs/heads/main:refs/remotes/origin/main
git -C "$repo" diff --exit-code 21748a3b9baeb405b620878778409115fef93a78 d5a936464277b74f3ff377661ef20213db3c4dd3
git -C "$repo" ls-tree -r --name-only d5a936464277b74f3ff377661ef20213db3c4dd3
```

Publicação concluída. A pendência experimental segue documentada no relatório de avaliação independente. A missão usou somente Git e os documentos já preparados.
