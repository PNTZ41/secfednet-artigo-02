# Auditoria de capturas, suporte e métricas · BENIGN × DDoS

26/11/2026, 11:34:25, Belém. **Conclusão:** o acervo consultado não fornece capturas independentes com as duas classes e o contrato de 81 features para ajuste, calibração e validação. O único dia compatível com DDoS identificado no inventário corrigido é a sexta reservada. A aritmética da dose pode ser examinada no histórico. A elegibilidade nas futuras capturas e o efeito dos três métodos continuam indeterminados. [Proposta auditada](RELATORIO_2026-11-26_11-21-13_BRT_proposta_protocolo_ddos.md).

## Evidência por fonte

Inspeção do checkout, incluindo a árvore local ignorada, índices NPZ, configurações, fichas e manifestos. Os caminhos das duas raízes históricas indicadas no acervo (origem local e VM) não existem neste ambiente. Os resultados abaixo têm como limite esse material acessível. [Acervo da expansão](../../../../docs/artigo-01/expansao-2026-11-25/ACERVO.json).

| Captura CICIDS2017 corrigida | BENIGN finitos | DDoS não-Attempted | Uso para este protocolo |
|---|---:|---:|---|
| Segunda | 371.621 | 0 | Só oferece negativos |
| Terça | 315.106 | 0 | Patator não pertence à classe DDoS |
| Quarta | 319.119 | 0 | DoS e Heartbleed têm outros rótulos |
| Quinta | 288.171 | 0 | Sem denominador para recall DDoS ou BSR |
| Sexta | 288.544 | 95.144 | Inventário apenas. Teste reservado |

Contagens derivadas do inventário não-Attempted e das cinco exclusões BENIGN por não finitude. Outros rótulos foram deixados fora das duas colunas. A tabela não implica que os CSVs brutos estejam disponíveis. [Suporte original por membro](../../../../docs/artigo-01/expansao-2026-11-25/fonte/inventario_cinco_capturas.json) · [Exclusões com captura e registro](../../../../docs/artigo-01/expansao-2026-11-25/candidato/exclusoes_qualidade.json).

- **CNN corrigida.** Conferi igualdade literal e posicional dos 81 nomes distintos no contrato da CNN, nos dois contratos da expansão e nas listas embutidas nos manifestos de validação e split cronológico. Isso verifica os esquemas declarados. A compatibilidade de uma nova captura ainda exige a mesma definição, unidade, sentido e extração das medidas. [Contrato CNN](../../../../integracao/artigo-01/contrato-cnn/contrato.json) · [Contrato candidato](../../../../docs/artigo-01/expansao-2026-11-25/fonte/contrato_candidato.json).
- **MachineLearningCSV de Gabriel.** 97.718 BENIGN e 128.027 DDoS, 78 atributos, cabeçalho repetido e ausência de IP, protocolo e timestamp. A ficha remete ao mesmo cenário de sexta à tarde do CICIDS2017. Hash e número de linhas diferentes documentam outra exportação, sem estabelecer outra campanha. Não há base local para mapear integralmente os 81 atributos ou parear eventos entre exportações. [Ficha original](../../../../SecFedNet_CICIDS2017_entrega/ficha_CICIDS2017.md).
- **UNSW-NB15.** Pacote documental com 42 features e Normal 56.000/37.000 em treino/teste. O rótulo disponível é DoS (12.264/4.089). Falta evidência de DDoS identificado e de equivalência com as 81 medidas. Os CSVs citados no manifesto não estão na entrega. [Contagens nominais](../../../../docs/artigo-01/expansao-2026-11-25/gabriel/unsw-nb15/results/class_counts_multiclass.csv) · [Auditoria e procedência](../../../../docs/artigo-01/expansao-2026-11-25/GABRIEL.md).
- **Reprodução em VM.** Configurações e resultados da repetição descrevem o mesmo recorte e partição. Repetir um ensaio em outra máquina não fornece observações de outra campanha. [Reprodução histórica](../../../../docs/reproducao-vm/2026-11-24/README.md).

## Independência por fluxo, sessão e campanha

No pool histórico da sexta, o ajuste tem 163.096 BENIGN e 40.155 DDoS, a validação tem 40.776 e 10.039, respectivamente. O manifesto informa oito BENIGN excluídos do ajuste e zero interseções ajuste–validação por grupo, vetor bruto e entrada final float32. Recalculei a interseção de IDs de linha nos NPZ: zero para ajuste×validação, ajuste×teste e validação×teste. O relatório histórico também informa zero grupos comuns entre pool e teste. Esses conjuntos provêm da mesma captura. A validação histórica serviu à escolha do limiar e à medição de desempenho. Não há uma terceira captura de calibração identificada. [Auditoria histórica](../../cnn-validacao/particao/auditoria.json) · [Uso histórico do limiar](../../cnn-scaffold/README_20.md).

Na expansão, a auditoria semanal relata ausência de evento comum por quíntupla com timestamp, mas recorrência de grupos de conexão entre dias. A chave bidirecional não contém tempo e pode reaparecer em sessões distintas. Mesmo após exclusão sequencial de vetores brutos, a representação float32 tem 44/46/9 chaves comuns para treino×quinta, treino×sexta e quinta×sexta. Esses números abrangem o cenário semanal BENIGN/ATTACK. Sem arquivos de captura independentes, identificadores de sessão/campanha e limites temporais verificáveis, não se pode atestar ausência de sobreposição para o novo recorte. [Definições de evento e grupo](../../../../docs/artigo-01/expansao-2026-11-25/METODO_AUDITORIA.md) · [Interseções](../../../../docs/artigo-01/expansao-2026-11-25/candidato/intersecoes_representacoes.csv).

## Suporte por cliente e viabilidade da dose

Ordem dos vetores: clientes 0, 1, 2, 3, 4. Contagens somente para o **pool histórico de ajuste** de 203.251 fluxos. A seed da partição, e não a dos pesos, governa essas contagens. Dose teórica inteira = piso(DDoS locais / 20), logo o mínimo é 20 DDoS no cliente 0.

| Modelo/partição | BENIGN nos cinco clientes | DDoS nos cinco clientes | Dose inteira / DDoS do cliente 0 | Natureza da evidência |
|---|---|---|---|---|
| 23/2305 | 4.388 / 14.293 / 6.097 / 43.289 / 95.029 | 217 / 5.689 / 203 / 7.460 / 26.586 | 10 / 217 (4,61%) | Suporte registrado e reconciliado |
| 41/4105 | 7.087 / 62.215 / 40.957 / 39.814 / 13.023 | 1.246 / 3.276 / 16.901 / 4.165 / 14.567 | 62 / 1.246 (4,98%) | Projeção no mesmo pool histórico |
| 89/8905 | 102.961 / 36.066 / 6.851 / 17.132 / 86 | 7.849 / 13.640 / 10.413 / 6.997 / 1.256 | 392 / 7.849 (4,99%) | Projeção no mesmo pool histórico |

Na primeira linha, conferi tamanhos e hashes dos cinco vetores de índices e cobertura única de todo o ajuste. O JSON fornece os rótulos agregados. Os NPZ de clientes contêm índices, sem rótulo individual para uma recontagem independente. Nas outras linhas reproduzi apenas os tamanhos das partições pela ordem de sorteios da rotina local (Dirichlet, multinomial e permutação por classe), a partir das duas contagens totais. A reprodução com NumPy 2.4.6 recupera integralmente a linha 2305. As projeções não identificam fluxos reais nem certificam uma execução histórica nas seeds 4105/8905. No desenvolvimento independente, a viabilidade segue **pendente nas três seeds**. [Configuração e suporte registrados](../../cnn-scaffold/ensaio-20-rodadas/execucao/configuracao.json) · [Regra de distribuição](../../../../integracao/artigo-01/avaliar_piloto.py).

## Revisão das métricas

Fixar seed, captura, rodada e limiar calibrado no controle limpo. Seja D o conjunto de IDs de **todos os DDoS reais da avaliação** com versão marcada válida de acordo com a regra congelada. Registrar também o número de DDoS previstos no manifesto, pares ausentes ou inválidos e suas causas. Usar o mesmo D para todos os braços. Para modelo m, versão original o ou marcada t, definir B(m,v,i)=1 quando o fluxo i é previsto BENIGN e 0 quando é previsto DDoS. C é o controle limpo contemporâneo e A é o braço em comparação.

1. **BSR bruta sobre todos os DDoS marcados.** BSR(m) = soma de B(m,t,i) em D / |D|. Inclui os DDoS já perdidos pelo controle. Publicar BSR(A), BSR(C) e a diferença pareada BSR(A) − BSR(C) em pontos percentuais. A diferença usa a mesma versão marcada e desconta a taxa de erros do controle nesse denominador.
2. **Aumento condicionado entre fluxos reconhecidos.** Na rodada 10 fixar E como os IDs de D com B(C,o,i)=B(C,t,i)=0. O aumento de saídas BENIGN na entrada marcada é a média em E de B(A,t,i) − B(C,t,i). Na rodada de seleção equivale ao número previsto BENIGN por A na versão marcada dividido por |E|. Publicar |E|, |D| e |E|/|D|. Esse resultado mede a diferença entre braços sob o pareamento prescrito. Pode incluir perda geral do detector após a intervenção.
3. **Componente associado ao marcador.** No mesmo E, medir a média de [B(A,t,i) − B(A,o,i)] − [B(C,t,i) − B(C,o,i)]. Na rodada 10 o termo do controle é zero por construção. Publicar a tabela pareada original×marcado em cada braço, incluindo ganhos e perdas de detecção. Assim, um DDoS perdido por A nas duas versões conta no item 2 e tem contribuição zero no item 3.
4. **Persistência e incerteza.** Na rodada 20 manter os IDs de E definidos na rodada 10 e usar as predições contemporâneas de C: seu termo pode agora diferir de zero. Mostrar resultados por método, seed e captura, com contagens, FPR BENIGN e recall DDoS nas entradas originais. Para denominador vazio, declarar “não estimável”. Fixar precisão mínima e unidade de incerteza por sessão/campanha antes da leitura de scores. Atribuição à intervenção depende do pareamento de pesos, dados, limiar e demais condições.

Não há outputs marcados pareados do controle e dos três braços neste acervo. Matrizes limpas agregadas não determinam |E|, BSR ou aumentos. Nenhum desses desfechos foi estimado nesta missão.

## Decisões pendentes

Identificar fontes com BENIGN e DDoS para três funções disjuntas: ajuste dos pesos, calibração do limiar e validação da comparação com limiar congelado. Se a validação for usada para decidir o protocolo, distinguir também uma avaliação final intocada. Preservar a sexta reservada. Exigir procedência e períodos de sessão/campanha, conferir os 81 atributos e suas unidades, auditar coincidências nas representações bruta e consumida, documentar conflitos de rótulo e recontar suportes após as exclusões. Só então conferir a partição efetiva e o denominador mínimo no cliente 0 por seed. Fixar cobertura de pares e critério de precisão antes de medir BSR.

## Registro e reprodução

Git inicial/final: branch `integracao/artigo-01`, HEAD `4cc2727`. Índice local rastreado já modificado e `.idea/` já não rastreada ao iniciar. Escritos nesta missão: este relatório, `secfednet-local/artigo-01/INDEX.md` e `secfednet-local/artigo-01/STATUS.md`. Instrução local encontrada: `AGENTS.md` da raiz. `.agents/` e `.codex/` vazios. Não houve treino, download, execução de ataque nem inferência. A sexta foi consultada apenas nos metadados previamente produzidos.

Comandos de inspeção: git status, git rev-parse, rg --files --hidden --no-ignore, rg, cat, ls, head, tail, TZ=America/Belem date, leitura JSON/NPZ em Python e git diff --check. A partir da raiz, este comando reproduz a comparação dos esquemas, a cobertura dos índices, as contagens não-Attempted antes do filtro de finitude e a projeção dos suportes.

```sh
python3 -B - <<'PY'
import json, hashlib
from pathlib import Path
import numpy as np
h=Path('secfednet-local/artigo-01')
e=Path('docs/artigo-01/expansao-2026-11-25')
run=h/'cnn-scaffold/ensaio-20-rodadas/execucao'
def read(p): return json.loads(p.read_text())
cfg=read(run/'configuracao.json')
a=read(h/'cnn-validacao/particao/auditoria.json')
f=read(Path('integracao/artigo-01/contrato-cnn/contrato.json'))['ordem_features']
assert len(f)==len(set(f))==81
for p in ('contrato_candidato.json','contrato_features_referencia.json'):
    assert read(e/'fonte'/p)['ordem_features']==f
with np.load(h/'cnn-validacao/particao/manifesto_validacao.npz') as m, np.load(h/'cicids2017-corrigido/split_cronologico.npz') as g:
    assert m['ordem_features'].tolist()==g['ordem_features'].tolist()==f
    print('IDs ajuste/val, ajuste/teste, val/teste:',*[len(np.intersect1d(x,y)) for x,y in [(m['ajuste'],m['validacao']),(m['ajuste'],g['linhas_teste']),(m['validacao'],g['linhas_teste'])]])
with np.load(run/'clientes.npz') as z:
    idx=[]
    for p in cfg['particoes']:
        v=z['cliente_'+str(p['cliente'])]
        assert len(v)==p['total'] and hashlib.sha256(v.tobytes()).hexdigest()==p['indices_no_treino_sha256']
        idx.extend(v.tolist())
    assert sorted(idx)==list(range(sum(a['ajuste'].values())))
for c in read(e/'fonte/inventario_cinco_capturas.json')['csvs']:
    print(c['arquivo'],c['nao_attempted']['BENIGN'],c['nao_attempted'].get('DDoS',0))
for seed in (2305,4105,8905):
    rng=np.random.default_rng(seed)
    while True:
        parts=[]
        for k in ('BENIGN','DDoS'):
            n=a['ajuste'][k]
            parts.append(rng.multinomial(n,rng.dirichlet(np.full(5,0.5))))
            rng.permutation(n)
        if np.all(np.sum(parts,axis=0)>0): break
    if seed==2305:
        assert parts[0].tolist()==[p['suporte']['BENIGN'] for p in cfg['particoes']]
        assert parts[1].tolist()==[p['suporte']['DDoS'] for p in cfg['particoes']]
    print(seed,*[v.tolist() for v in parts],int(parts[1][0])//20)
PY
```
