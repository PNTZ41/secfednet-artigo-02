# Artigo 02 · Fluxo FedAvg e validação defensiva sintética

26/11/2026, 15:59:52, Belém (UTC−03). Escopo concluído: leitura do fluxo federado, identificação da referência limpa e teste defensivo em memória. Gradient Scaling, Model Replacement e Constrain-and-Scale são categorias de ameaça para a integridade do treinamento. O relatório descreve pontos de controle do servidor e do cliente. A implementação e as instruções operacionais desses backdoors ficam fora do escopo entregue. [Proposta de avaliação do controle](RELATORIO_2026-11-26_11-39-50_BRT_avaliacao_fedavg_limpo.md).

## Dois caminhos Flower

| Caminho | Mensagem do cliente | Agregação no servidor | Uso |
|---|---|---|---|
| `ClienteCNN.fit` e `FedAvgLocal.aggregate_fit` | Carrega o `state_dict` global, treina localmente com Adam e BCE com logits e devolve os pesos completos, `num_examples` e perda. | Exige os cinco IDs esperados, ordena resultados e delega à média FedAvg ponderada por número de exemplos. | Piloto CNN histórico. |
| `ClienteSGD.fit` e `Estrategia.aggregate_fit` | Carrega pesos globais, executa SGD local e devolve deltas de pesos, `num_examples` e perda. `dc` só está presente no caminho SCAFFOLD. | Exige cinco resultados, verifica IDs, tamanho do payload e número de exemplos, e usa `agregar`. No FedAvg-SGD a média é uniforme por cliente e aplicada aos pesos globais com taxa global 1. | Referência limpa de 20 rodadas do Artigo 02. |

O `ProxyLocal` encaminha as chamadas do cliente no mesmo processo. A validação de registros locais do cliente em `Estrategia.aggregate_fit` depende desse arranjo. Em uma avaliação de integridade, o servidor precisa validar o que recebe contra seu próprio estado e esquema. O agregador aritmético `agregar` usa `np.stack` e médias, sem um contrato explícito de forma, dtype e finitude para cada tensor recebido. [Cliente e estratégia Adam](../../../artigo-01/cnn-flower/treinar_cnn.py#L101) · [Cliente e estratégia SGD](../../../artigo-01/cnn-scaffold/experimentar_scaffold.py#L39) · [Aritmética da agregação](../../../artigo-01/cnn-scaffold/scaffold.py#L78).

A CNN recebe 81 valores em ordem fixa, padronizados com estatísticas do ajuste. Duas Conv1d com ReLU e pooling para comprimento quatro alimentam uma camada de 16 ativações. A cabeça produz um logit de DDoS. O BCE local recebe esse logit, enquanto a avaliação aplica sigmoide e limiar. O monitoramento histórico ocorre em `EstrategiaCurva.aggregate_fit` após a atualização global. A proposta do Artigo 02 separa calibração de avaliação. O limiar histórico de validação interna não serve de limiar validado na avaliação independente. [CNN](../../../artigo-01/cnn-flower/cnn1d.py#L17) · [Monitoramento da rodada](../../../artigo-01/cnn-scaffold/experimentar_20.py#L48).

## Controles defensivos por risco

| Categoria | Observação defensiva |
|---|---|
| Gradient Scaling | Examinar variações anormais de magnitude em relação ao histórico limpo por camada e por cliente. Magnitude elevada tem causas legítimas e deve ser tratada como sinal de auditoria. |
| Model Replacement | Auditar a alteração no modelo global após cada agregação e preservar as identidades dos estados anterior e posterior para investigação e restauração. |
| Constrain-and-Scale | Combinar verificações de integridade do payload com métricas comportamentais em calibração independente. Atualizações formalmente válidas e de norma comum ainda podem alterar o comportamento do modelo. |

Uma primeira camada modular pode validar número, forma, dtype e finitude dos tensores no recebimento, antes de alterar o estado global. Separar os registros de diagnóstico das decisões de aceitação e preservar o controle FedAvg limpo para comparação. As verificações de formato protegem o contrato de dados. A avaliação de desempenho e integridade requer controles adicionais, suporte de classe e uma política de rejeição definida previamente.

## Teste em memória

Isolei via AST a função `agregar` existente, sem importar o módulo de treino. Com cinco clientes sintéticos e duas formas de tensor em float32, a função produziu os pesos esperados `[12, -4]` e `[[5]]`, preservou os pesos de entrada e copiou os controles sem alterá-los no modo FedAvg. Um validador defensivo separado, executado em memória antes do agregador, rejeitou quatro casos de teste: quantidade incorreta de tensores, forma incorreta, dtype divergente e NaN. O validador não foi incorporado à implementação. NumPy estava disponível, PyTorch e Flower não estavam instalados no ambiente consultado. O resultado cobre somente a aritmética e a checagem de contrato, sem executar ciclo Flower ou CNN.

## Decisões pendentes

- Confirmar se o próximo ensaio usa novos pesos ajustados nas partições independentes ou avalia transferência com o checkpoint histórico congelado. Para transferência, obter `rodada-20.pt` e o `checkpoint.pt` que contém média e escala, validar hashes e paridade dos extratores. [Auditoria dos artefatos](RELATORIO_2026-11-26_14-52-12_BRT_acervo_fedavg_extratores.md).
- Fechar os manifestos por sessão/campanha e o suporte por classe e cliente após exclusões. Fixar seeds, ordem dos lotes, orçamento e associação cliente/partição. A configuração de referência é 20 rodadas, cinco clientes, participação integral, SGD 0,01, lote 512 e uma época local. O manifesto histórico é evidência de referência, sem uso como entrada nesta missão. [Configuração de referência](../../../artigo-01/cnn-scaffold/protocolo_20.json).
- Definir limiar no conjunto de calibração, com recall e FPR no conjunto independente. Para avaliação defensiva, registrar previamente a reação a payload inválido, critérios para sinalizar desvios e o custo em falsos alertas sob partições heterogêneas. A sexta permanece reservada.

## Registro e reprodução

Branch inicial e final `integracao/artigo-01`, HEAD `4cc2727`. O índice rastreado do Artigo 01 já aparecia modificado e `.idea/` já aparecia não rastreada. Alterados sob `secfednet-local/artigo-02/`: este relatório, `INDEX.md` e `STATUS.md`. Nenhum código de treino foi editado. Instrução local `AGENTS.md`. Pastas `.agents/` e `.codex/` vazias. Usei `git status`, `git rev-parse`, `cat`, `head`, `rg`, `ls`, `sed`, data em America/Belem, detecção local de módulos e o comando abaixo. O teste não usa dataset, checkpoint, treino completo, inferência ou a sexta reservada.

```sh
python3 -B - <<'PY'
import ast
from pathlib import Path

import numpy as np

path = Path("secfednet-local/artigo-01/cnn-scaffold/scaffold.py")
tree = ast.parse(path.read_text())
func = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "agregar")
scope = {"np": np}
exec(compile(ast.Module(body=[func], type_ignores=[]), str(path), "exec"), scope)
agregar = scope["agregar"]

def validar_formato(globais, delta):
    if len(delta) != len(globais):
        raise ValueError("Quantidade de tensores")
    for a, b in zip(globais, delta, strict=True):
        if a.shape != b.shape or a.dtype != b.dtype or not np.isfinite(b).all():
            raise ValueError("Formato ou finitude")

f = np.float32
globais = [np.array([10, -2], f), np.array([[3]], f)]
controles = [np.zeros_like(a) for a in globais]
deltas = [[np.array([i, -i], f), np.array([[2]], f)] for i in range(5)]
for d in deltas:
    validar_formato(globais, d)
novos, cg = agregar(globais, controles, deltas, [], 5)
assert np.array_equal(novos[0], np.array([12, -4], f))
assert np.array_equal(novos[1], np.array([[5]], f))
assert all(np.array_equal(a, b) and not np.shares_memory(a, b)
           for a, b in zip(controles, cg, strict=True))
assert np.array_equal(globais[0], np.array([10, -2], f))
assert np.array_equal(globais[1], np.array([[3]], f))
print("FedAvg-SGD: média uniforme, controles preservados e entradas intactas")
cases = {
    "quantidade": deltas[0][:1],
    "shape": [np.zeros((1, 2), f), deltas[0][1]],
    "dtype": [deltas[0][0].astype(np.float64), deltas[0][1]],
    "NaN": [np.array([np.nan, 0], f), deltas[0][1]],
}
for nome, d in cases.items():
    try:
        validar_formato(globais, d)
    except ValueError:
        print("Validador em memória rejeitou", nome)
    else:
        raise AssertionError(nome)
PY
```
