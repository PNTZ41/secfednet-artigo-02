# Auditoria metodológica do FedAvg limpo · Artigo 01

26/11/2026, 11:04:56, Belém (UTC−03). Objetivo: estabelecer o erro limpo e a cobertura da expansão antes de comparar Gradient Scaling, Model Replacement e Constrain-and-Scale. Auditoria documental das tabelas existentes, com reconciliação aritmética. Nenhum treino, download ou inferência.

## O que está comprovado

O comparador é a CNN-1D binária BENIGN/ATTACK de **cinco rodadas** da expansão do CICIDS2017 corrigido. Usa 81 atributos, normalização ajustada só no treino, cinco clientes Dirichlet α=0,5 com participação integral, uma época local, Adam 0,001 reiniciado por cliente/rodada e lote 512. As seeds 23/41/89 variam inicialização, partição e ordem conjuntamente. A comparação centralizada pareia pesos iniciais, máscaras e exposições (5.922.120), com pequenas diferenças no número de passos. O ensaio de integração de uma rodada tem 68.372 FN e 3.535 VP na quinta e é uma referência distinta. O pacote histórico BENIGN/DDoS também tem outro alvo. [Método](../../../../docs/artigo-01/expansao-2026-11-25/METODOLOGIA.md) · [Orçamento por seed](../../../../docs/artigo-01/expansao-2026-11-25/vm/tabelas/orcamento_por_seed.csv) · [Integração](../../../../docs/artigo-01/expansao-2026-11-25/baseline-kubuntu/metricas_quinta.csv).

### Erro limpo por seed

Quinta-feira, cenário principal, limiar fixo 0,5. Cada FN é um fluxo ATTACK classificado como BENIGN. O denominador da taxa de falsos negativos (FNR) é sempre 71.907 ataques reais. As seeds avaliam os mesmos registros, portanto somar seus FN não conta fluxos únicos. [Matrizes e métricas por seed](../../../../docs/artigo-01/expansao-2026-11-25/vm/tabelas/resultados_por_seed.csv).

| Seed | VN | FP | FN | VP | FNR | Recall ATTACK | FPR | AP | Macro-F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 23 | 287.956 | 215 | 65.102 | 6.805 | 90,536% | 9,464% | 0,0746% | 0,7049 | 0,5353 |
| 41 | 288.095 | 76 | 70.613 | 1.294 | 98,200% | 1,800% | 0,0264% | 0,5487 | 0,4630 |
| 89 | 288.120 | 51 | 71.449 | 458 | 99,363% | 0,637% | 0,0177% | 0,4614 | 0,4511 |

A máscara de sensibilidade exclui da quinta 31.649 fluxos BENIGN. Conserva todos os ATTACK, seus FN/VP e o número de FP em cada seed. O denominador da FPR cai de 288.171 para 256.522. Trata-se de reavaliação das mesmas predições sob outra máscara. As tabelas incluem ainda precisão ATTACK e média/desvio amostral entre seeds. [Variação entre seeds](../../../../docs/artigo-01/expansao-2026-11-25/vm/tabelas/variacao_entre_seeds.csv).

### Cobertura por captura e tipo

| Captura | Papel e tipos ATTACK retidos | Evidência de desempenho do FedAvg de cinco rodadas |
|---|---|---|
| Segunda | Treino, apenas BENIGN | Sem matriz por captura. Recall ATTACK sem denominador. |
| Terça | Treino, FTP-Patator e SSH-Patator | Inventário de suporte, sem avaliação independente. |
| Quarta | Treino, quatro tipos DoS e Heartbleed | Inventário de suporte, sem avaliação independente. |
| Quinta | Validação, dois tipos Infiltration e três Web | Matrizes, AP, precisão, macro-F1, recall e FPR por seed/cenário. Por tipo há suporte e recall binário. |
| Sexta | Teste reservado, Botnet, Portscan e DDoS | Apenas inventário e diagnósticos de qualidade e sobreposição. Desempenho permanece em aberto. |

Separados 11.979 registros Attempted. Após remover cinco linhas BENIGN com valores não finitos, treino/validação/teste têm 1.184.424 / 360.078 / 543.490 fluxos. As famílias nominais positivas da quinta diferem das de treino. Infiltration - Portscan concentra 71.767 dos 71.907 positivos (99,805%). A média de recall descreve sobretudo essa captura. [Inventário das cinco capturas](../../../../docs/artigo-01/expansao-2026-11-25/fonte/inventario_cinco_capturas.json) · [Manifesto](../../../../docs/artigo-01/expansao-2026-11-25/candidato/manifesto_candidato.json).

| Tipo real na quinta | Suporte | FN seed 23 | FN seed 41 | FN seed 89 |
|---|---:|---:|---:|---:|
| Infiltration - Portscan | 71.767 | 64.962 | 70.475 | 71.309 |
| Infiltration | 36 | 36 | 36 | 36 |
| Web Attack - Brute Force | 73 | 73 | 71 | 73 |
| Web Attack - SQL Injection | 13 | 13 | 13 | 13 |
| Web Attack - XSS | 18 | 18 | 18 | 18 |

Por tipo, VP = suporte × recall arredondado ao inteiro e FN = suporte − VP. Nos dois cenários, as somas reproduzem exatamente as matrizes. Para BENIGN a coluna de recall mede especificidade. Para tipo ausente o CSV registra NA. [Recall nominal](../../../../docs/artigo-01/expansao-2026-11-25/vm/tabelas/recall_por_tipo.csv).

### Coincidências e conflitos

Chaves distintas de vetores de 81 atributos compartilhadas entre conjuntos, na ordem treino×quinta / treino×sexta / quinta×sexta:

| Cenário e representação | Três contagens |
|---|---|
| Principal, bruto float64 | 19.965 / 20.437 / 10.728 |
| Principal, entrada efetiva float32 | 19.919 / 20.392 / 10.701 |
| Sensibilidade após exclusão sequencial, bruto float64 | 0 / 0 / 0 |
| Mesma sensibilidade, normalizado float64 | 39 / 40 / 9 |
| Mesma sensibilidade, entrada efetiva float32 | 44 / 46 / 9 |

Já há coincidências após normalizar em float64. Na sensibilidade, a conversão seguinte acrescenta pares antes distintos em 6 / 7 / 0 chaves. Esse incremento não se calcula subtraindo os totais de chaves, pois algumas se fundem. As 44 chaves do primeiro par abrangem 305 linhas de treino e 57 de quinta. Igualdade na entrada do modelo não identifica sozinha uma duplicata do evento de rede. [Interseções e multiplicidades](../../../../docs/artigo-01/expansao-2026-11-25/candidato/intersecoes_representacoes.csv) · [Incremento da conversão](../../../../docs/artigo-01/expansao-2026-11-25/candidato/colisoes_incrementais_float32.csv).

No cenário principal há 0 / 1 / 13 chaves com conflito **binário** e 0 / 1 / 110 com conflito **nominal**, tanto no vetor bruto como na entrada float32. Infiltration - Portscan e Portscan podem divergir nominalmente e concordar como ATTACK. Na sensibilidade, os três pares têm zero conflito cruzado nominal ou binário nas representações auditadas, apesar das coincidências residuais. A identidade de evento por quíntupla e timestamp não cruza os conjuntos. Excluir toda conexão bidirecional recorrente eliminaria os três tipos Web da validação. [Conflitos por representação](../../../../docs/artigo-01/expansao-2026-11-25/candidato/conflitos_representacoes.csv) · [Simulações por classe](../../../../docs/artigo-01/expansao-2026-11-25/fonte/auditoria_referencia/simulacoes_por_classe.csv).

## O que permanece inconclusivo

As tabelas resolvem **quantos** fluxos o modelo perde ao fim da quinta rodada. Elas não identificam **quais** são nem quantos coincidem entre seeds. O comparador salva scores finais de quinta no acervo da execução. Para identificar fluxos é preciso alinhar scores, rótulos, máscaras e índices originais. As tabelas finais tampouco dão uma trajetória de FN por rodada. Permanece sem estimativa o efeito causal das coincidências, da partição e de qualquer backdoor sobre esses erros. [Código de avaliação](../../../../docs/artigo-01/expansao-2026-11-25/controle/comparar_cnn.py) · [Localização do acervo](../../../../docs/artigo-01/expansao-2026-11-25/ACERVO.json).

## Verificações antes dos três métodos

1. Fixar o cenário principal e a análise de sensibilidade. Quantificar por tipo e por linha o efeito de aplicar a exclusão na representação float32 consumida. Documentar a regra para conflitos binários e nominais, preservar a procedência e verificar o suporte depois de qualquer exclusão. Fazer essas decisões com treino e validação e manter a sexta reservada para a avaliação final.
2. Recuperar do acervo os scores limpos de quinta por seed e o manifesto de índices. Conferir hashes, ordem e unicidade de (captura, registro), rótulo, tipo, máscara, limiar e reprodução das matrizes. Congelar os identificadores dos VP limpos antes da comparação. Para uma análise por rodada, registrar também a referência limpa da rodada correspondente.
3. Pré-especificar a comparação pareada nas mesmas seeds, partições, pesos iniciais, orçamento e exemplos. Para medir perda de detecção, contar entre os ATTACK corretamente detectados pelo controle quantos passam a BENIGN na condição avaliada. Publicar numerador e denominador por seed/tipo e o resultado do modelo limpo sobre as mesmas entradas de avaliação. Registrar também FN preexistentes, transições inversas, recall e FPR no tráfego limpo. Uma porcentagem bruta de saídas BENIGN incluiria até 99,363% de erros já presentes na quinta.
4. Identificar denominadores vazios como **não estimável**. Na quinta, por exemplo, nenhum dos três modelos detecta um único SQL Injection. A seed 41 detecta somente dois Brute Force. Relatar as contagens por captura/tipo e a variação entre seeds. Para ampliar cobertura, definir validações adicionais dentro do desenvolvimento antes de congelar o protocolo. A sexta permanece reservada.

## Registro e reprodução da auditoria

Branch inicial e final `integracao/artigo-01`, HEAD `4cc2727`, com upstream local `origin/integracao/artigo-01`. No início, apenas `.idea/` aparecia como não rastreada. Ao final, além dela, há a edição do índice já rastreado. Arquivos escritos sob `secfednet-local/artigo-01/`: este relatório, `INDEX.md` (link) e `STATUS.md` (estado e próximo passo). O relatório e o status são ignorados pela regra `/secfednet-local/`. Instrução aplicável: `AGENTS.md` da raiz. Diretórios `.agents/` e `.codex/` vazios. Nenhum outro AGENTS.md ou SKILL.md local identificado.

Foram usados `git status --short --branch`, `git rev-parse --short HEAD`, `git ls-files`, `rg`, `ls`, `cat`, `head`, `tail`, `cut`, `awk` e `TZ=America/Belem date` para inspeção. Alterações apenas documentais. O comando abaixo, executado da raiz, reproduz a conferência das seis linhas FedAvg usando apenas os CSVs publicados. Saída por seed nos dois cenários: 65.102/6.805, 70.613/1.294 e 71.449/458 (FN/VP). Os 231 checks de reprodução entre ambientes são evidência histórica da expansão e não foram reexecutados nesta missão.

```bash
python3 -B - <<'PY'
import csv
from pathlib import Path

p = Path("docs/artigo-01/expansao-2026-11-25/vm/tabelas")
def ler(nome):
    with (p / nome).open() as f:
        return list(csv.DictReader(f))

tipos = ler("recall_por_tipo.csv")
for r in ler("resultados_por_seed.csv"):
    if r["metodo"] != "fedavg":
        continue
    linhas = [t for t in tipos if all(t[k] == r[k] for k in ("seed", "metodo", "cenario"))
              and t["tipo"] != "BENIGN" and int(t["suporte"]) > 0]
    n = sum(int(t["suporte"]) for t in linhas)
    vp = sum(round(int(t["suporte"]) * float(t["recall_classe_binaria"])) for t in linhas)
    assert n == int(r["suporte_ATTACK"]) and vp == int(r["VP"]) and n-vp == int(r["FN"])
    assert int(r["VN"]) + int(r["FP"]) == int(r["suporte_BENIGN"])
    print(r["seed"], r["cenario"], n-vp, vp, f"{100*(n-vp)/n:.3f}%")
PY
```
