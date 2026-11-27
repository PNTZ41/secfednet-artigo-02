# Reprodução do SecFedNet Artigo 01 na VM

Ensaio de duas rodadas FedAvg-SGD × SCAFFOLD, commit `0b38f255af6f22e4642c584c0f0e09b15ef9263e`. O ensaio começou em 24/11/2026 às 22:11:30 BRT (America/Belem, UTC−03:00).

## Resultado

O CICIDS2017 corrigido passou na verificação de SHA-256. Os 50.815 scores float32 de cada método coincidiram bit a bit com os de referência. A quantidade de scores diferentes e a diferença absoluta máxima foram zero. O SHA-256 de `execucao/resultados.json` também coincidiu com o registrado no manifesto histórico.

| Método | Limiar na validação | Matriz [[VN, FP], [FN, VP]] | FPR | Recall DDoS | Macro-F1 |
| --- | ---: | --- | ---: | ---: | ---: |
| FedAvg-SGD | 0,41333019733428955 | [[40375, 401], [10032, 7]] | 0,983422% | 0,069728% | 0,443460920 |
| SCAFFOLD | 0,4026653468608857 | [[40776, 0], [10039, 0]] | 0% | 0% | 0,445196580 |

Ao limiar fixo de 0,5, ambos classificaram todos os exemplos como BENIGN, com matriz `[[40776, 0], [10039, 0]]`, recall e FPR zero e macro-F1 de 0,445196580. As métricas da tabela são exploratórias. O limiar foi escolhido na mesma validação em que foi medido. A validação interna continha 40.776 BENIGN e 10.039 DDoS. O teste global, a validação de μ, o ensaio de vinte rodadas e a inferência do ZIP ficaram fora do escopo.

O teste escalar reproduziu a segunda rodada bit a bit após retomada em outro processo. Os dois métodos compartilharam inicialização, partições e ordem de minibatches, com cinco clientes, 203.251 exemplos por rodada e 800 passos por método nas duas rodadas. Os pesos da primeira rodada coincidiram bit a bit entre os métodos e os controles locais persistiram entre as rodadas. A recarga dos checkpoints da CNN em outro processo reproduziu os scores e as métricas. Os volumes brutos coincidiram com a referência. Cada método recebeu e enviou 45.960 bytes de parâmetros. O SCAFFOLD recebeu e enviou 45.960 bytes adicionais de controles. A medição cobre os arrays da simulação em processo.

## Comparação com a referência

Comparei os arquivos incluídos em `cnn-scaffold/ensaio-01/execucao/` e os hashes em `cnn-scaffold/SHA256_ARTEFATOS`, ambos sob `secfednet-local/artigo-01/`. Dos 27 hashes históricos, 21 coincidiram, incluindo `clientes.npz`, os estados das rodadas 0–2, o teste escalar, o pareamento, os scores, as métricas e o log de recarga. Os cinco arrays de índices de clientes também coincidiram na comparação direta.

As seis diferenças foram `configuracao.json`, os dois `checkpoint.pt`, os dois `treino.json` e `tempo.json`. Na configuração, o único campo diferente foi `versoes.plataforma`, com kernel `7.0.0-44-generic` na VM e `7.0.0-43-generic` na referência. Em cópias temporárias dos dois checkpoints, substituir apenas `configuracao_sha256` pelo hash histórico reproduziu exatamente os hashes históricos dos checkpoints. Os arquivos de treino diferiram apenas pelo tempo e pelo hash do checkpoint. O tempo total histórico está disponível nesta entrega somente como hash.

## Ambiente e tempos

Ubuntu 26.04.1 LTS, Linux 7.0.0-44-generic x86-64, glibc 2.43, Intel Core i3-10100 com quatro CPUs lógicas visíveis. CPython 3.14.4, PyTorch 2.12.1+cpu, Flower 1.32.0, NumPy 2.3.5, curl 8.18.0. O binário `uv` usado na preparação era 0.13.10 e a versão instalada dentro do ambiente pelo lock foi 0.11.33. O `uv pip check` confirmou a compatibilidade dos 41 pacotes instalados. SHA-256 de `requirements.lock`: `af00bc8c6bf5cd033462e8d2a5ac1ce6bada4e22dde698d85380183941ca5d44`.

| Etapa | VM | Referência |
| --- | ---: | ---: |
| Download bem-sucedido do ZIP (HTTP 200, 343.549.013 bytes) | 20,209 s | — |
| Sincronização bem-sucedida do lock | 8,287 s | — |
| Treino FedAvg-SGD | 2,961 s | 2,580 s |
| Treino SCAFFOLD | 3,053 s | 2,648 s |
| Leitura e preparação dos dados, treino dos dois métodos e avaliação inicial (`execucao/tempo.json`) | 22,814 s | — |
| Script completo, incluindo teste escalar e recarga em novo processo | 70,47 s | — |

No script completo, `/usr/bin/time` mediu 73,47 s de CPU em modo usuário, 2,52 s em modo sistema e RSS máximo de 1.147.572 KiB. Os tempos internos estão incluídos nos 70,47 s.

As primeiras tentativas no sandbox falharam por restrição de DNS no download e no acesso ao PyPI. O cache padrão do `uv` também estava em sistema de arquivos somente leitura. Usei `UV_CACHE_DIR=/tmp/secfednet-uv-cache` e executei as operações de rede com permissão ampliada. O `uv` copiou os arquivos quando o hardlink entre sistemas de arquivos falhou. Todos esses bloqueios foram resolvidos.

## Comandos de reprodução

A partir de `/home/williian/secfednet-repro/codigo`, com Python 3.14.4 e uv disponíveis. Em uma árvore já preparada, use o ZIP após a conferência de SHA-256 e selecione outro destino de execução.

```bash
set -e
git status --short --branch --untracked-files=all
git rev-parse HEAD
cat AGENTS.md
git show 0b38f25:README.md
git show 0b38f25:integracao/artigo-01/README.md
sha256sum -c SHA256_ENTREGA --quiet

base=secfednet-local/artigo-01
dataset="$base/cicids2017-corrigido/CICIDS2017_improved.zip"
mkdir -p "$(dirname "$dataset")"
if test ! -e "$dataset"; then
  time curl --fail --location --silent --show-error --connect-timeout 15 --retry 2 \
    https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip \
    --output "$dataset"
fi
printf '%s  %s\n' 97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883 "$dataset" |
  sha256sum --check

export UV_CACHE_DIR=/tmp/secfednet-uv-cache
venv="$base/cnn-flower/.venv"
if test ! -x "$venv/bin/python"; then
  uv --no-config venv --python 3.14.4 --no-python-downloads "$venv"
fi
time uv --no-config pip sync --strict --python "$venv/bin/python" \
  --default-index https://pypi.org/simple "$base/cnn-flower/requirements.lock"
uv --no-config pip check --python "$venv/bin/python"

export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
destino="$base/execucoes/scaffold-curto-vm-$(TZ=America/Belem date +%Y%m%d-%H%M%S)"
/usr/bin/time -f '%e s reais, %U s CPU usuário, %S s CPU sistema, RSS máximo %M KiB' \
  bash "$base/cnn-scaffold/reproduzir.sh" "$destino"
uv --no-config pip freeze --python "$venv/bin/python" > "$destino/dependencias-instaladas.txt"
```

Para repetir as comparações desta execução, a partir da raiz do repositório:

```bash
base=secfednet-local/artigo-01
destino=secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="integracao/artigo-01:$base/cicids2017-corrigido:$base/cnn-flower:$base/cnn-flower-entrega:$base/cnn-flower-clientes:$base/cnn-fedprox:$base/cnn-validacao"
"$base/cnn-flower/.venv/bin/python" -B "$destino/comparar.py" "$destino"
"$base/cnn-flower/.venv/bin/python" -B "$destino/verificar_checkpoints.py" "$destino"
sha256sum -c SHA256_ENTREGA --quiet
git status --short --branch --untracked-files=all
```

## Arquivos e estado final

- [Pasta nova da execução](codigo/secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130). Contém [métricas](codigo/secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130/execucao/resultados.json), [comparação por hash e por campo](codigo/secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130/comparacao_referencia.json), [checagem dos checkpoints](codigo/secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130/verificacao_checkpoints.txt), [controle escalar](codigo/secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130/teste_controles/resultado.json), [log da recarga](codigo/secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130/recarga.log) e [inventário dos pacotes](codigo/secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130/dependencias-instaladas.txt).
- ZIP verificado em `secfednet-local/artigo-01/cicids2017-corrigido/CICIDS2017_improved.zip`. Ambiente de treino em `secfednet-local/artigo-01/cnn-flower/.venv/`. Ambos são ignorados pelo Git.
- Registros locais em `secfednet-local/artigo-01/execucoes/`. Usei `INDEX.md` e `STATUS.md` nesse diretório porque o índice da entrega em `secfednet-local/artigo-01/INDEX.md` é versionado e consta no manifesto. Cópia do relatório no destino solicitado `/home/williian/secfednet-repro/RELATORIO_REPRODUCAO_VM.md`.
- A instrução local encontrada foi `/home/williian/secfednet-repro/codigo/AGENTS.md`. As pastas `.agents/` e `.codex/` do repositório estavam vazias. A busca na árvore do repositório encontrou somente esse `AGENTS.md` entre os arquivos de instruções e skills procurados. Nenhuma skill ou subagente foi usado.
- Git no início e no fim em HEAD destacado no commit `0b38f25`, com status limpo. Os 89 arquivos de `SHA256_ENTREGA` passaram antes e depois. Os fontes versionados e os arquivos da entrega de Gabriel foram preservados. Foram criados somente o dataset, ambiente, saídas, scripts locais de comparação e registros. Não houve stage, commit ou push.

Pendências do escopo solicitado: nenhuma. Próximo passo: anexar o relatório à revisão da reprodução.

