> Documento histórico do piloto logístico com 78 features. No pacote atual, o CSV de Gabriel é obtido separadamente; o conteúdo abaixo descreve o acervo original. A entrada atual para a CNN de 81 features e os ensaios está no [README da entrega](../../README.md).

# SecFedNet · Artigo 01 · Integração de 23/11/2026

A cópia local do CICIDS2017 contém 225.745 registros (`BENIGN` 97.718 e `DDoS` 128.027). O SHA-256 `6ff1580f5f81c0ae28a26f7631721018577f5f7c5e0feac28b795fcfe7b411ee` coincide com o da ficha de Gabriel. A ficha atribui o CSV à distribuição do Canadian Institute for Cybersecurity. O pacote local contém o CSV, a ficha e o script de caracterização. [Ficha de Gabriel](../../SecFedNet_CICIDS2017_entrega/ficha_CICIDS2017.md) · [Origem e integridade](artefatos/origem.json)

## Reprodução

Execute da raiz do repositório. A caracterização usa a biblioteca padrão. O piloto foi validado com Python 3.14.4 e NumPy 2.3.5. [Dependência do piloto](requirements.txt)

```bash
CSV=SecFedNet_CICIDS2017_entrega/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
INT=integracao/artigo-01
ART="$INT/artefatos"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
sha256sum -- "$CSV"
python3 -B SecFedNet_CICIDS2017_entrega/caracterizar_csv.py "$CSV" --saida "$ART/caracterizacao.json"
python3 -B "$INT/piloto_fedavg.py" treinar "$CSV" "$ART"
python3 -B "$INT/piloto_fedavg.py" prever "$ART/checkpoint.npz" "$ART/exemplo_entrada.json" > "$ART/exemplo_saida.json"
cat "$ART/exemplo_saida.json"
```

## Contrato do piloto

A entrada é um objeto JSON com `features`, um vetor de 78 números finitos brutos na ordem literal do CSV, excluindo ` Label`. A ordem completa está em `ordem_features` nas métricas e no checkpoint. Preserve os espaços do cabeçalho e as duas posições de ` Fwd Header Length` (35 e 56, base 1). O preditor aplica a média e o desvio padrão salvos no checkpoint. [Ordem completa das features](artefatos/metricas.json)

O exemplo usa o registro de dados 18.889 do CSV. Os quatro primeiros valores são `80`, `79731718`, `8` e `5`. Seu rótulo real é `DDoS`. [Entrada completa](artefatos/exemplo_entrada.json)

```json
{"classe_id": 1, "classe": "DDoS", "score": 0.9667606982280192}
```

O mapa é `0 = BENIGN` e `1 = DDoS`. `score` é a saída sigmoide do modelo para `DDoS`, entre 0 e 1, sem calibração. O limiar é `0.5` inclusive para `DDoS`. O score continua referindo-se a `DDoS` quando a classe prevista é `BENIGN`. [Saída salva após recarregar o checkpoint](artefatos/exemplo_saida.json)

## Resultado e artefatos

O piloto usa regressão logística binária, três clientes simulados em CPU, oito rodadas FedAvg e dois passos locais por rodada. A agregação pondera pelo número de registros de cada cliente. Antes da divisão estratificada com semente 23, o treino retira 34 linhas com valores não finitos e 2.629 repetições de vetores numéricos. A padronização usa estatísticas calculadas só no treino.

O treino usou 178.467 registros. Nos 44.615 registros de teste do mesmo recorte, a acurácia foi 97,88%, com 934 falsos positivos e 12 falsos negativos. O checkpoint recarregado em um novo processo reproduziu o score calculado em memória. A avaliação cobre somente o recorte de sexta-feira à tarde. Embeddings **[PENDENTE]**.

| Artefato | Conteúdo |
| --- | --- |
| [caracterizacao.json](artefatos/caracterizacao.json) | Hash, rótulos exatos, contagens e diagnósticos do CSV bruto |
| [origem.json](artefatos/origem.json) | Procedência documentada e identificação da cópia local |
| [checkpoint.npz](artefatos/checkpoint.npz) | Pesos, intercepto, normalização, ordem das features, classes e limiar |
| [metricas.json](artefatos/metricas.json) | Divisão por cliente e classe, matriz de confusão e previsão de referência |
