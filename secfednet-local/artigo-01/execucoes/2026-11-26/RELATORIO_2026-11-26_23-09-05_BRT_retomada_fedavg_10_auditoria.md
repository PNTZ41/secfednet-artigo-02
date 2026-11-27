# Artigo 01 · Retomada limpa da rodada 10 e auditoria FedAvg-SGD

26/11/2026, 23:09:05, Belém (UTC−03). Objetivo: partir do estado da rodada 9, verificar uma rodada limpa contra a referência da VM e validar as contribuições no servidor antes da agregação. **A auditoria passou nos testes sintéticos. A reprodução com dados parou na checagem de insumos ausentes.**

## Fluxo e referência

O ensaio histórico `experimentar_20.py treinar` começa nos pesos da seed 23. Ele regenera as cinco partições Dirichlet (seed 2305), confere os vetores de índices contra o ensaio curto, e confere hashes e ordem dos 81 atributos. Cada cliente recebe os pesos globais, usa BCE com logits e SGD de uma época, lote 512, taxa 0,01, sem momentum ou estado de otimizador entre rodadas, e devolve deltas. O servidor ordena os clientes por ID e aplica a média uniforme de deltas. A seed dos lotes é `23 + 100 × rodada + cliente`.

O ensaio salva o número de rodada, os pesos e os controles em cada `rodada-NN.pt`. A verificação posterior recarrega esse estado com `weights_only=True` em CPU para comparar pesos, scores e hashes. O CLI histórico inicia um treino novo ou verifica saídas. A nova entrada usa o estado da rodada 9, exige que a próxima seja a 10 e usa as seeds 1023–1027 com 400 passos no total (9, 40, 13, 100 e 238 por cliente). O modelo final `checkpoint.pt` fornece somente a referência de média, escala e ordem. Seus pesos da rodada 20 não inicializam a retomada. [Ensaio histórico](../../cnn-scaffold/experimentar_20.py) · [Cliente e estratégia Flower](../../cnn-scaffold/experimentar_scaffold.py) · [Serialização](../../cnn-scaffold/scaffold.py).

O carregador histórico reabre o ZIP e lê `friday.csv` antes de selecionar os índices de ajuste e validação, e calcula as estatísticas em float64 somente no ajuste. A entrada nova usa uma exportação limitada aos dois subconjuntos internos, na ordem dos IDs do manifesto. Ela recalcula a média e o desvio populacional sobre o ajuste para conferir os parâmetros originais (escala zero vira 1), usa a média e escala do checkpoint e converte o resultado para float32. A nova entrada não lê a captura inteira nem as linhas do teste reservado. [Carregador histórico](../../cnn-validacao/validar_mu.py#L113).

Conferi os SHA-256 de `clientes.npz` (`bbb35ecd842ddf7924e6b9d884d096a36bac01a258affaee27af34b592ddaffb`) e `manifesto_validacao.npz` (`bb710d6492ac83456b61ba8469d06f6729bf063ba586a557b0165a701173339f`) contra a configuração. Verifiquei que os cinco clientes cobrem os 203.251 índices do ajuste exatamente uma vez, que não há IDs comuns com os 50.815 da validação e que o manifesto declara as 81 colunas na ordem esperada. [Configuração da referência](../../cnn-scaffold/ensaio-20-rodadas/execucao/configuracao.json).

## Artefatos e impedimento

A pasta `/home/kali/PycharmProjects/SecFedNet-artefatos/fedavg-rodada20/` existe e estava vazia. Os artefatos da tabela também não foram encontrados no checkout, nos projetos vizinhos ou nas montagens consultadas. Os valores abaixo foram conferidos contra o inventário da VM. Sem os binários, não houve recálculo de seus hashes nem leitura da média/escala. O SHA do `checkpoint.pt` histórico local é diferente do SHA da VM, pois o arquivo contém um hash de configuração. O caminho novo exige a variante da VM indicada pelo usuário. [Inventário da VM](../../../../docs/reproducao-vm/2026-11-24/ACERVO.json) · [Manifesto local](../../cnn-scaffold/SHA256_ARTEFATOS_20).

| Nome esperado na pasta de artefatos | SHA-256 esperado da VM |
|---|---|
| `rodada-09.pt` | `2bd04013797041c291013ac82c32ad2e25ce3e8110b5d80f24cf97bf1ffdd062` |
| `checkpoint.pt` | `4e73b24cf7042eace103969787d86f07084ddc4eb558a01fe3bcf32562898922` |
| `rodada-10.pt` | `8be0ec6a061c77d5c3e806d4c6ca8b3983b514ab89cff374011d392e914808da` |
| `scores_validacao_10.npy` | `56506368572736c705ac4f94bb4b9c6c4a905fbcea72d858387ceddeb550e198` |

Falta ainda `/home/kali/PycharmProjects/SecFedNet-artefatos/fedavg-rodada20/ajuste_validacao_interna.npz`, exportação apenas das linhas autorizadas do ensaio. Deve conter `ordem_features`, `ids_ajuste`, `x_ajuste`, `y_ajuste`, `ids_validacao`, `x_validacao` e `y_validacao`. Os `ids` devem reproduzir a ordem de `ajuste` e `validacao` no manifesto original. Os `x` são os 81 valores brutos finitos em float64. Os `y` são rótulos 0=BENIGN e 1=DDoS. Obter junto à exportação o hash do NPZ e sua procedência. O ambiente disponível tem NumPy, sem PyTorch ou Flower. A execução precisa do ambiente da referência descrito no lock. Nenhum treino, score, estado da rodada ou diretório de resultado foi produzido.

## Implementação e validação

- [auditar_atualizacoes.py](../../cnn-scaffold/auditar_atualizacoes.py) valida o conjunto de participantes e, por cliente, a quantidade, forma, dtype e finitude dos tensores antes de chamar o agregador histórico. Registra a norma L2 de todos os deltas de pesos de cada cliente usando float64 para a soma de quadrados. Qualquer contribuição inválida interrompe a rodada.
- [retomar_fedavg_10.py](../../cnn-scaffold/retomar_fedavg_10.py) é a entrada separada para reproduzir uma rodada, preservando as fontes e manifestos históricos. Reusa `ClienteSGD.fit` em processo local com a configuração da rodada 10, verifica seeds, ordem dos lotes e passos, reúne as contribuições do lado do servidor e chama a agregação auditada. Reusa a inferência histórica somente na validação interna. Compara conteúdo binário dos pesos e dos scores com as referências da VM e grava estado, scores e `auditoria.json` em destino novo. A nova entrada chama diretamente os clientes Flower locais e o agregador. Ela não reinicia o contador de um novo `Server.fit`.
- A validação sintética passou com cinco clientes e duas formas de tensor. A saída auditada foi idêntica bit a bit à agregação original e as normas foram 0, 5, 10, 15 e 20. Um agregador sentinela verificou que quantidade errada, forma incompatível, dtype distinto, NaN e infinito foram rejeitados antes de qualquer agregação. A entrada de retomada foi exercitada até a checagem de insumos. O caminho de treino e a comparação com a VM continuam sem execução.

## Reprodução e registro

Próximo passo: obter os quatro binários e a exportação interna, ativar o ambiente registrado e executar o comando abaixo. A saída é criada somente após a rodada e a comparação. A sexta reservada segue fora de uso.

```sh
BASE_10=secfednet-local/artigo-01
ARTEFATOS_10="$HOME/PycharmProjects/SecFedNet-artefatos/fedavg-rodada20"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 FLWR_TELEMETRY_ENABLED=0
export PYTHONPATH="integracao/artigo-01:$BASE_10/cicids2017-corrigido:$BASE_10/cnn-flower:$BASE_10/cnn-flower-entrega:$BASE_10/cnn-flower-clientes:$BASE_10/cnn-fedprox:$BASE_10/cnn-validacao"
"$BASE_10/cnn-flower/.venv/bin/python" -B "$BASE_10/cnn-scaffold/retomar_fedavg_10.py" \
  "$ARTEFATOS_10" "$ARTEFATOS_10/ajuste_validacao_interna.npz" \
  "$BASE_10/execucoes/2026-11-26/retomada-10-auditada"
```

Teste sintético efetuado da raiz, com NumPy e sem importar PyTorch ou Flower:

```sh
python3 -B - <<'PY'
import ast
from pathlib import Path
import sys

import numpy as np

pasta = Path("secfednet-local/artigo-01/cnn-scaffold")
sys.path.insert(0, str(pasta))
from auditar_atualizacoes import agregar_auditado

p = pasta / "scaffold.py"
tree = ast.parse(p.read_text())
funcao = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "agregar")
env = {"np": np}
exec(compile(ast.Module(body=[funcao], type_ignores=[]), str(p), "exec"), env)
controle = env["agregar"]
globais = [np.zeros(2, dtype=np.float32), np.ones((2, 1), dtype=np.float32)]
controles = [np.zeros_like(x) for x in globais]
deltas = {i: [np.array([3*i, 4*i], dtype=np.float32),
              np.zeros((2, 1), dtype=np.float32)] for i in reversed(range(5))}
pesos, c, auditoria = agregar_auditado(globais, controles, deltas, range(5), controle)
esperados = controle(globais, controles, [deltas[i] for i in range(5)], [], 5)
assert [a.tobytes() for a in pesos + c] == [a.tobytes() for a in esperados[0] + esperados[1]]
assert auditoria == [{"cliente": i, "norma_l2_delta_pesos": i*5.0} for i in range(5)]
print("Válidos: agregação bit a bit, cinco normas corretas")

def nao_agregar(*args):
    raise AssertionError("A agregação recebeu entrada inválida")

invalidos = {
    "quantidade": deltas[0][:1],
    "dimensões": [np.zeros((1, 2), dtype=np.float32), deltas[0][1]],
    "dtype": [deltas[0][0].astype(np.float64), deltas[0][1]],
    "NaN": [np.array([np.nan, 0], dtype=np.float32), deltas[0][1]],
    "inf": [np.array([np.inf, 0], dtype=np.float32), deltas[0][1]],
}
for nome, delta in invalidos.items():
    try:
        agregar_auditado(globais, controles, {**deltas, 4: delta}, range(5), nao_agregar)
    except ValueError as erro:
        assert "Cliente 4" in str(erro)
        print(f"{nome}: rejeitado antes de agregar")
    else:
        raise AssertionError(nome)
PY
```

Estado inicial/final do Git: branch `integracao/artigo-01`, HEAD `4cc2727`. O índice do Artigo 01 já estava modificado e `.idea/` já aparecia não rastreada. Foram acrescentados os dois módulos citados e este relatório. Atualizados `INDEX.md` e `STATUS.md` do Artigo 01. Os novos módulos e o relatório ficam sob a regra de ignore de `secfednet-local/`. Instrução consultada em `AGENTS.md`, diretórios `.agents/` e `.codex/` vazios. Comandos executados: `git status`, `git rev-parse`, `cat`, `ls`, `rg`, `find`, `sed`, `date` em America/Belem, Python para comparação com o inventário, hashes e inspeção NPZ/AST, teste sintético acima, entrada de retomada com Python do sistema (interrompida na checagem de arquivos), conferência de links e `git diff --check`.
