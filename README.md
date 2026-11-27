# SecFedNet · Artigo 01 · Entrada para equipes consumidoras

Esta entrega contém o código e as referências dos ensaios reproduzidos, o contrato da CNN e a documentação de integração. Receba os dois pacotes: `secfednet-artigo01-codigo-v1.tar.gz` e `pacote-inferencia/secfednet-cnn1d-v1.zip`. Extraia o TAR em `codigo/`, mantendo a pasta `pacote-inferencia/` como irmã. Este README é a raiz de `codigo/`.

| Uso | Entrada |
| --- | --- |
| Consumir classe, score e embedding | ZIP separado da CNN e contrato abaixo; funciona sem dataset. |
| Reproduzir os ensaios | Três comandos de treino/avaliação abaixo, com o CICIDS2017 corrigido. |
| Consultar o piloto logístico de Gabriel | [Documento histórico de 78 features](integracao/artigo-01/README.md) e [ficha original](SecFedNet_CICIDS2017_entrega/ficha_CICIDS2017.md). |

## Integridade e seleção

Da raiz `codigo/`, antes de criar ambiente ou baixar dados:

```bash
sha256sum -c SHA256_ENTREGA
```

[Lista final de 90 arquivos](LISTA_ARQUIVOS.txt) · [Seleção e separação dos pacotes](SELECAO_FINAL.md) · [Índice da entrega](secfednet-local/artigo-01/INDEX.md). Os 70 arquivos da seleção auditada foram preservados e complementados. Os manifestos SHA antigos registram o acervo histórico; o manifesto deste conjunto é `SHA256_ENTREGA`, que cobre os outros 89 arquivos do TAR. Um nível acima, `SHA256_DISTRIBUICAO` confere os arquivos reais da distribuição, incluindo os dois pacotes. O próprio arquivo de manifesto é excluído de seu hash.

## Inferência CNN, sem dataset

[ZIP de inferência](../pacote-inferencia/secfednet-cnn1d-v1.zip), 13.489 bytes, SHA-256:
`e7d042b38c77b96bef54533302bef817d6b8a4a8e55b717bac7b32f98b5b6014`.

Checkpoint dentro dele: `checkpoint_cnn1d.pt`, 12.949 bytes, SHA-256:
`37db7d4f6d0123786cc4ed5227d670edb1344c07089e8ff6910c6446e57400f3`.

É a CNN original FedAvg de três rodadas em CPU com cinco clientes e Adam lr=0,001, treinada com 254.074 fluxos. O ZIP foi preservado. Os ensaios posteriores de FedAvg-SGD e SCAFFOLD geram seus próprios checkpoints e limiares exploratórios; eles ficam nos resultados da reprodução.

Entrada: `{"features": [81 números finitos brutos]}`, na ordem literal de [contrato.json](integracao/artigo-01/contrato-cnn/contrato.json). A [tabela numerada de todas as features](integracao/artigo-01/contrato-cnn/CONTRATO.md) documenta a ordem e a normalização. O preditor aplica média e desvio do treino salvos no checkpoint, em float64, e converte a entrada da CNN para float32. Não normalize previamente. Timestamp e identificadores ficam fora da entrada.

| Saída | Contrato |
| --- | --- |
| `classe_id`, `classe` | 0=BENIGN, 1=DDoS. Limiar **0,5**, inclusive para DDoS. |
| `score` | Sigmoide do logit DDoS, em [0,1], sem calibração probabilística; refere-se sempre a DDoS. |
| `embedding` | 16 ativações ReLU da camada `embedding.1`, antes da cabeça de classificação. Não são probabilidades nem vetor normalizado. |

Exemplo: [entrada real completa](integracao/artigo-01/contrato-cnn/exemplo_entrada.json) → classe `DDoS`, score `0.987495481967926` e embedding de 16 valores; [saída completa](integracao/artigo-01/contrato-cnn/exemplo_saida.json). O limiar do ZIP é fixo; o teto empírico de FPR de 1% dos ensaios não é uma garantia desse pacote.

Plataforma validada: Linux x86-64, glibc 2.43, CPython 3.14.4 e PyTorch 2.12.1+cpu. O lock é específico desse Python/plataforma. `uv` e Python devem estar disponíveis.

Da raiz `codigo/`, com `../inferencia-cnn/` ainda inexistente:

```bash
python3 -m zipfile -e ../pacote-inferencia/secfednet-cnn1d-v1.zip ../inferencia-cnn
cd ../inferencia-cnn
sha256sum -c SHA256SUMS
uv --no-config venv --python 3.14.4 --no-python-downloads .venv
uv --no-config pip sync --strict --python .venv/bin/python --default-index https://pypi.org/simple requirements.lock
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -I -B cnn1d.py checkpoint_cnn1d.pt exemplo_entrada.json > saida_verificada.json
cmp -- exemplo_saida.json saida_verificada.json
cd ../codigo
```

O código carrega o checkpoint em CPU com `weights_only=True`. A inferência usa somente os oito arquivos do ZIP e as dependências instaladas.

## Dados e reprodução dos ensaios

Origem: [distribuição corrigida CNS2022 dos autores](https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/). Arquivo `CICIDS2017_improved.zip`, 343.549.013 bytes; o código lê `friday.csv` diretamente do ZIP. A ficha de Gabriel documenta outra versão, MachineLearningCSV/UNB com 78 features. O esquema da CNN usa as **81 features da versão corrigida**.

O dataset não é entregue no TAR nem no ZIP de inferência. Para obtê-lo, da raiz `codigo/`:

```bash
mkdir -p secfednet-local/artigo-01/cicids2017-corrigido
curl --fail --location https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip --output secfednet-local/artigo-01/cicids2017-corrigido/CICIDS2017_improved.zip
sha256sum --check <<'SHA'
97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883  secfednet-local/artigo-01/cicids2017-corrigido/CICIDS2017_improved.zip
SHA
```

Criar ambiente de treino separado do ambiente de inferência:

```bash
uv --no-config venv --python 3.14.4 --no-python-downloads secfednet-local/artigo-01/cnn-flower/.venv
uv --no-config pip sync --strict --python secfednet-local/artigo-01/cnn-flower/.venv/bin/python --default-index https://pypi.org/simple secfednet-local/artigo-01/cnn-flower/requirements.lock
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
bash secfednet-local/artigo-01/cnn-validacao/reproduzir.sh ../resultados/validacao
bash secfednet-local/artigo-01/cnn-scaffold/reproduzir.sh ../resultados/scaffold-curto
bash secfednet-local/artigo-01/cnn-scaffold/reproduzir_20.sh ../resultados/scaffold-20
```

Os destinos de resultados devem ser novos. Dependências de treino: Python 3.14.4, PyTorch 2.12.1+cpu, Flower 1.32.0 e NumPy 2.3.5, com 41 pacotes fixados no lock. Os comandos preservam os dados e referências entregues; ambiente e dataset são preparação de execução, fora da seleção.

Os três ensaios usam a validação interna: 203.251 fluxos de ajuste e 50.815 de validação, com grupos disjuntos, índices congelados e normalização só no ajuste. São reproduzidos os expurgos já auditados. O teste global permanece congelado, sem nova inferência. A escolha do limiar e a medição na mesma validação tornam as métricas exploratórias.

| Rotina | Saídas no destino |
| --- | --- |
| Validação | Manifesto/auditoria/protocolo regenerados; quatro modelos, scores, métricas, seleção de μ/limiar, configuração e logs. |
| SCAFFOLD curto | Teste dos controles em duas rodadas, pesos e controles, checkpoints, scores, métricas, bytes e recarga. |
| SCAFFOLD 20 | Estados 0–20, scores e curvas por rodada, perdas, recall sob FPR≤1%, bytes acumulados, comparação 20/20 e 20/10 e verificação independente. |

As saídas são geradas separadamente da entrega de código. Os comandos não recriam o ZIP de inferência original ou manifestos históricos. O [inventário auditado](secfednet-local/artigo-01/cnn-validacao/PRIMEIRO_COMMIT.md) e os resultados de referência foram mantidos para rastreabilidade.

Esta é uma entrega local para revisão. Nenhum stage, commit, push, PR ou publicação acompanha os pacotes.
