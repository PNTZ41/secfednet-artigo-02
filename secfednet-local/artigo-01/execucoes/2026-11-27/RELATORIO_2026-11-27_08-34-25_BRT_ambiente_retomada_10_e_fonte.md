# Artigo 01 · Ambiente e insumos da retomada limpa da rodada 10

27/11/2026, 08:34:25, Belém (UTC−03). Objetivo: conferir os quatro artefatos da VM, preparar o ambiente, exportar ajuste e validação interna e reproduzir somente a rodada 10. **Ambiente de referência pronto e artefatos íntegros. Rodada ainda bloqueada pela ausência do ZIP corrigido ou da exportação interna.**

## Artefatos e manifesto

Os quatro arquivos em `~/PycharmProjects/SecFedNet-artefatos/fedavg-rodada20/` passaram em `sha256sum -c SHA256SUMS`. Recalculei cada hash e comparei também com os registros da VM e os valores fixados na entrada de retomada. [Inventário original](../../../../docs/reproducao-vm/2026-11-24/ACERVO.json) · [Entrada de retomada](../../cnn-scaffold/retomar_fedavg_10.py).

| Arquivo | SHA-256 calculado e confirmado |
|---|---|
| `rodada-09.pt` | `2bd04013797041c291013ac82c32ad2e25ce3e8110b5d80f24cf97bf1ffdd062` |
| `checkpoint.pt` | `4e73b24cf7042eace103969787d86f07084ddc4eb558a01fe3bcf32562898922` |
| `rodada-10.pt` | `8be0ec6a061c77d5c3e806d4c6ca8b3983b514ab89cff374011d392e914808da` |
| `scores_validacao_10.npy` | `56506368572736c705ac4f94bb4b9c6c4a905fbcea72d858387ceddeb550e198` |

Com `torch.load(weights_only=True, map_location="cpu")`, verifiquei os números de rodada, os hashes dos oito tensores de pesos contra `rodadas.json` e os controles zerados. O checkpoint final contém o método e o contrato esperados, média e escala finitas de 81 posições em float64, escala positiva e hashes de ambos os vetores correspondentes à configuração. Os scores de referência são 50.815 valores finitos float32. Este passo conferiu arquivos arquivados. A equivalência de uma nova rodada permaneceu sem teste. [Configuração e registros](../../cnn-scaffold/ensaio-20-rodadas/execucao/configuracao.json).

Conferi os SHA-256 do manifesto interno e das partições de clientes. Os 203.251 IDs de ajuste e os 50.815 de validação são distintos e pertencem ao treino cronológico. A interseção da união dessas máscaras com os IDs reservados é zero. A ordem das 81 colunas coincide entre manifesto, split cronológico e checkpoint. A checagem usou apenas metadados de índices do teste. [Manifesto original](../../cnn-validacao/particao/manifesto_validacao.npz) · [Protocolo de validação](../../cnn-validacao/particao/protocolo.json).

## Fonte e exportação

Falta `secfednet-local/artigo-01/cicids2017-corrigido/CICIDS2017_improved.zip`, SHA-256 esperado `97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`, 343.549.013 bytes. A busca local e nas montagens acessíveis não encontrou o ZIP, `friday.csv` ou `ajuste_validacao_interna.npz`. A tentativa de obter o ZIP oficial falhou na resolução DNS no Kali, inclusive fora do sandbox. O índice dos autores lista o arquivo. Nenhum ZIP foi gravado e nenhum dado do teste reservado foi lido. [Índice oficial de distribuição](https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/).

Acrescentei `exportar_ajuste_validacao.py`. Ele exige os SHA-256 da fonte e dos manifestos, confirma ausência de IDs reservados nas máscaras, localiza as linhas pelo número original do registro CSV e materializa apenas os IDs internos. Features float64 e rótulos inteiros ficam alinhados na ordem exata do manifesto, mesmo que essa ordem difira da ordem de leitura. O exportador confere 81 colunas e suporte por classe antes de salvar. Um ZIP sintético de cinco registros confirmou ordem não monotônica do manifesto, alinhamento, formas, tipos e exclusão de uma linha reservada com campos que falhariam se fossem interpretados. O exportador ainda não foi testado com o ZIP real. [Exportador](../../cnn-scaffold/exportar_ajuste_validacao.py).

## Ambiente instalado

O ambiente `secfednet-local/artigo-01/cnn-flower/.venv-3.14.4/` contém CPython **3.14.4**, PyTorch **2.12.1+cpu**, Flower **1.32.0** e NumPy **2.3.5**. O `uv pip sync --strict` instalou as 41 entradas do lock e `uv pip check` passou. Os imports de `experimentar_20` e `experimentar_scaffold` passaram no ambiente exato. As versões conferem com a VM. O host de execução continua sendo Kali.

Primeiro instalei o lock em `.venv/` com o Python 3.14.7 do sistema. Como `uv python install 3.14.4` expirou, obtive a mesma distribuição pré-compilada vinculada à versão do uv por HTTPS direto no GitHub. O tarball recebido tem SHA-256 `fe9a9c32d13870af632cbac3dfc7528ae53597e94472aa4c7d6a42e8166136cd`. Extraí o interpretador em `cnn-flower/python-referencia/python/` e criei o ambiente exato. Obtive também o tarball-fonte oficial e conferi seu SHA-256 publicado, mas ele não foi usado na instalação. O ambiente exato é o indicado nos comandos abaixo. [Lock](../../cnn-flower/requirements.lock) · [Distribuição pré-compilada](https://github.com/astral-sh/python-build-standalone/releases/tag/20260414) · [CPython 3.14.4](https://www.python.org/downloads/release/python-3144/).

## Ponto de retomada

A chamada de retomada com o ambiente exato parou na checagem inicial por falta de `ajuste_validacao_interna.npz`, sem criar saída ou executar treino. Disponibilizar o ZIP corrigido acima ou uma exportação existente com procedência verificada. Os quatro artefatos e o ambiente já estão no Kali. Com o ZIP disponível, da raiz:

```sh
BASE_10=secfednet-local/artigo-01
PYTHON_10="$BASE_10/cnn-flower/.venv-3.14.4/bin/python"
ART_10="$HOME/PycharmProjects/SecFedNet-artefatos/fedavg-rodada20"
DADOS_10="$BASE_10/cicids2017-corrigido"
"$PYTHON_10" -B "$BASE_10/cnn-scaffold/exportar_ajuste_validacao.py" \
  "$DADOS_10/CICIDS2017_improved.zip" "$DADOS_10/ajuste_validacao_interna.npz"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 FLWR_TELEMETRY_ENABLED=0
export PYTHONPATH="integracao/artigo-01:$BASE_10/cicids2017-corrigido:$BASE_10/cnn-flower:$BASE_10/cnn-flower-entrega:$BASE_10/cnn-flower-clientes:$BASE_10/cnn-fedprox:$BASE_10/cnn-validacao:$BASE_10/cnn-scaffold"
"$PYTHON_10" -B "$BASE_10/cnn-scaffold/retomar_fedavg_10.py" \
  "$ART_10" "$DADOS_10/ajuste_validacao_interna.npz" \
  "$BASE_10/execucoes/2026-11-27/retomada-10-auditada"
```

A entrada existente compara pesos e scores bit a bit e registra o resultado em `auditoria.json`. Usar um destino novo para cada execução. A comparação real da rodada permanece pendente.

## Registro da missão

Git inicial/final em `integracao/artigo-01` e HEAD `4cc2727`. Índice rastreado já modificado e `.idea/` já não rastreada. Acrescentei o exportador, este relatório e os ambientes isolados, e atualizei `INDEX.md` e `STATUS.md`. O script de retomada e as fontes do ensaio histórico foram preservados. `AGENTS.md` é a instrução local aplicável, com `.agents/` e `.codex/` vazios.

Comandos executados: inspeção com `git status`, `git rev-parse`, `rg`, `find`, `ls`, `sed`, `cat` e data America/Belem. Verificação com `sha256sum -c SHA256SUMS`, leitura de JSON e NPZ e conferências com Python, PyTorch em CPU e `weights_only=True`. Instalação com `python -m venv`, `pip install -r requirements.lock`, tentativa de `uv python install 3.14.4`, `curl` e `tar` do interpretador pré-compilado, `uv pip sync --strict` e `uv pip check` com cache em `/tmp/secfednet-uv-cache`. Executados ainda teste sintético do exportador, checagem inicial da entrada de retomada, validação de links e `git diff --check`.
