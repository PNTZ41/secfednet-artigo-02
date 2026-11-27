# Artigo 01 · Conferência do recebimento para retomada da rodada 10

26/11/2026, 23:17:52, Belém. Objetivo: localizar a entrega do William, confirmar os SHA-256 no Kali e verificar as condições para reproduzir a rodada 10. A pasta `/home/kali/PycharmProjects/SecFedNet-artefatos/fedavg-rodada20/` continua vazia. O pacote informado na conversa não foi localizado no checkout, nos projetos vizinhos, em Downloads, Documentos, Desktop, `/mnt`, `/media` ou `/tmp`. A conferência termina na etapa de recebimento, antes de carregar o estado da rodada 9. [Relatório anterior](RELATORIO_2026-11-26_23-09-05_BRT_retomada_fedavg_10_auditoria.md).

## Artefatos e ambiente

Conferi que os quatro SHA-256 esperados no script coincidem com o inventário da VM. Nenhum dos arquivos estava disponível para recálculo ou cópia. [Inventário VM](../../../../docs/reproducao-vm/2026-11-24/ACERVO.json) · [Script de retomada](../../cnn-scaffold/retomar_fedavg_10.py).

| Arquivo | SHA-256 esperado da VM |
|---|---|
| `rodada-09.pt` | `2bd04013797041c291013ac82c32ad2e25ce3e8110b5d80f24cf97bf1ffdd062` |
| `checkpoint.pt` | `4e73b24cf7042eace103969787d86f07084ddc4eb558a01fe3bcf32562898922` |
| `rodada-10.pt` | `8be0ec6a061c77d5c3e806d4c6ca8b3983b514ab89cff374011d392e914808da` |
| `scores_validacao_10.npy` | `56506368572736c705ac4f94bb4b9c6c4a905fbcea72d858387ceddeb550e198` |

O Python esperado em `secfednet-local/artigo-01/cnn-flower/.venv/bin/python` está ausente. O Python 3.14.7 do Kali tem NumPy e não tem PyTorch nem Flower. O ambiente histórico registra CPython 3.14.4, PyTorch 2.12.1+cpu, Flower 1.32.0 e NumPy 2.3.5. [Lock](../../cnn-flower/requirements.lock) · [Ambiente do ensaio](../../cnn-scaffold/README_20.md).

## Exportação a solicitar ao William

Pedir `ajuste_validacao_interna.npz` da execução de referência, com a origem e a saída de `sha256sum`. O arquivo deve ser legível por `np.load(..., allow_pickle=False)` e conter somente ajuste e validação interna. Os scores são previsões. Para retomar, o cliente precisa dos atributos brutos e rótulos. Conferi formas e tipos dos IDs diretamente no [manifesto interno](../../cnn-validacao/particao/manifesto_validacao.npz).

| Chave | Forma | Tipo e conteúdo |
|---|---|---|
| `ordem_features` | `(81,)` | Strings Unicode na ordem e grafia do manifesto. O manifesto usa `<U26`. |
| `ids_ajuste` | `(203251,)` | Copiar `ajuste` do manifesto na ordem original, `int64`. |
| `x_ajuste` | `(203251, 81)` | `float64` finito, valores brutos na ordem indicada. |
| `y_ajuste` | `(203251,)` | Inteiros 0=BENIGN e 1=DDoS, alinhados aos IDs. Esperados 163.096 BENIGN e 40.155 DDoS. |
| `ids_validacao` | `(50815,)` | Copiar `validacao` do manifesto na ordem original, `int64`. |
| `x_validacao` | `(50815, 81)` | `float64` finito, valores brutos na ordem indicada. |
| `y_validacao` | `(50815,)` | Inteiros 0=BENIGN e 1=DDoS, alinhados aos IDs. Esperados 40.776 BENIGN e 10.039 DDoS. |

O script confere shapes e valores dos rótulos e não exige uma largura inteira específica para `y`. Usar inteiros `int64` é uma convenção suficiente. Para os IDs, usar as cópias exatas dos arrays existentes.

## Resultado e ponto de retomada

A comparação bit a bit ainda não ocorreu e não houve divergência observada entre resultados. O primeiro impedimento é a ausência dos arquivos no Kali. Quando o pacote estiver acessível, copiar e recalcular os quatro hashes, confirmar o NPZ e o ambiente, então usar o comando documentado no relatório anterior para executar somente a rodada 10 em outro diretório. A sexta reservada permaneceu fora do acesso.

Estado inicial/final do Git: branch `integracao/artigo-01`, HEAD `4cc2727`. O índice rastreado do Artigo 01 já estava modificado e `.idea/` já não rastreada. Alterados somente este relatório, `INDEX.md` e `STATUS.md`. Nenhum código, artefato de entrada ou saída da rodada foi alterado. Instrução aplicável em `AGENTS.md`, diretórios `.agents/` e `.codex/` vazios. Comandos executados: `git status`, `git rev-parse`, `ls`, `find`, `rg`, `cat`, `command -v`, `date` com America/Belem, detecção dos módulos nas instalações de Python, e os critérios de conferência abaixo. A conferência de links e `git diff --check` encerrou a missão.

```sh
python3 -B - <<'PY'
import hashlib
import json
from pathlib import Path
from sys import path

import numpy as np

base = Path("secfednet-local/artigo-01")
path.insert(0, str(base / "cnn-scaffold"))
from retomar_fedavg_10 import DIGESTS_VM, PARTICAO

acervo = json.loads(Path("docs/reproducao-vm/2026-11-24/ACERVO.json").read_text())
registros = {Path(a["path"]).name: a["sha256"] for a in acervo["arquivos"]
             if "/scaffold-20-vm-" in a["path"] and "/fedavg_sgd/" in a["path"]
             and Path(a["path"]).name in DIGESTS_VM}
assert registros == DIGESTS_VM
destino = Path.home() / "PycharmProjects/SecFedNet-artefatos/fedavg-rodada20"
for nome, esperado in registros.items():
    p = destino / nome
    if p.is_file():
        with p.open("rb") as arq:
            calculado = hashlib.file_digest(arq, "sha256").hexdigest()
        print(nome, calculado, "igual" if calculado == esperado else "divergente")
    else:
        print(nome, "ausente", "SHA-256 esperado", esperado)
print("NPZ disponível:", (destino / "ajuste_validacao_interna.npz").is_file())
with np.load(PARTICAO, allow_pickle=False) as m:
    for chave in ("ordem_features", "ajuste", "validacao"):
        print(chave, m[chave].shape, m[chave].dtype)
PY
```
