# SecFedNet — caracterização inicial do CICIDS2017

Consulta, cadastro, download e análise: 22/11/2026. Leitura integral concluída, sem limpeza dos dados.

## Origem e recorte

- Instituição: Canadian Institute for Cybersecurity, University of New Brunswick.
- Documentação: https://www.unb.ca/cic/datasets/ids-2017.html
- Cadastro oficial: https://cicresearch.ca/CICDataset/CIC-IDS-2017/
- Listagem após cadastro: https://cicresearch.ca/CICDataset/CIC-IDS-2017/browse.php?p=CIC-IDS-2017%2FCSVs
- ZIP: `MachineLearningCSV.zip`.
- Download oficial (pode exigir sessão de cadastro): https://cicresearch.ca/CICDataset/CIC-IDS-2017/download.php?file=CIC-IDS-2017%2FCSVs%2FMachineLearningCSV.zip
- CSV selecionado: `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv`.
- Membro exato do ZIP: `MachineLearningCVE/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv`.
- Cópia local: `data/raw/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv` (77.123.859 bytes).
- Recorte: sexta-feira, 07/07/2017, à tarde. A documentação situa o ataque DDoS entre 15h56 e 16h16. Essa é a janela do ataque, não necessariamente a extensão temporal de todos os registros do CSV.

## Acesso à distribuição

O endereço antigo de distribuição redirecionou para a página geral de datasets. O cadastro atual foi concluído com os dados autorizados pelo solicitante e disponibilizou a listagem de arquivos. O ZIP oficial completo foi salvo em `data/raw` (235.102.953 bytes). O servidor não aceita retomada por intervalos de bytes.

Uma cópia obtida anteriormente de um espelho público está separada em `data/espelho_nao_utilizado`. Ela não foi aberta nem usada na análise. Os resultados desta ficha foram calculados somente na cópia oficial.

## Uma linha real, explicada

Exemplo: registro de dados **18.884**, linha física **18.885**, contando o cabeçalho como linha 1. É a primeira ocorrência de `DDoS`, escolhida de forma determinística para mostrar um fluxo rotulado como ataque. Não é uma amostra aleatória nem uma linha necessariamente típica. A linha completa, com o cabeçalho original, está em `analise/exemplo_DDoS.csv`.

Os espaços iniciais dos cabeçalhos abaixo fazem parte do arquivo:

| Coluna literal | Valor original | Significado |
| --- | ---: | --- |
| ` Flow Duration` | 1293792 | Duração do fluxo em microssegundos: 1,293792 segundo. |
| ` Total Fwd Packets` | 3 | Três pacotes no sentido de ida, definido pelo primeiro pacote do fluxo. |
| ` Total Backward Packets` | 7 | Sete pacotes no sentido de volta. |
| ` Label` | DDoS | Classe atribuída pelo dataset ao fluxo. |

Em palavras: **essa linha resume um fluxo de comunicação que durou cerca de 1,294 segundo, teve três pacotes na ida e sete na volta e foi rotulado pelo dataset como `DDoS`.** Os três atributos ajudam a descrever o fluxo, mas isoladamente não demonstram que ele é um ataque. A porta de destino nessa mesma linha é 80, porém isso não comprova o protocolo de aplicação utilizado.

A coluna de classe é literalmente **` Label`**, com um espaço inicial. O arquivo não inclui IP de origem, IP de destino, protocolo nem timestamp. Por isso, não é possível identificar os participantes ou o instante desse fluxo apenas com esse CSV. Os IPs e a janela do cenário descritos na página institucional não foram atribuídos automaticamente a esta linha.

## Caracterização do arquivo original

| Medida | Resultado |
| --- | ---: |
| Linhas de dados, excluindo o cabeçalho | 225.745 |
| Colunas, incluindo o rótulo | 79 |
| Atributos fora a coluna de rótulo | 78 |
| Registros de largura incorreta | 0 |
| Registros vazios sem campos | 0 |
| Cabeçalhos repetidos como linhas de dados | 0 |

| Rótulo exato | Quantidade | Percentual do arquivo |
| --- | ---: | ---: |
| `BENIGN` | 97.718 | 43,2869% |
| `DDoS` | 128.027 | 56,7131% |
| Vazio ou somente espaços | 0 | 0% |
| **Total** | **225.745** | **100%** |

Os rótulos foram contados sem remoção de espaços, sem mudança de caixa e sem agrupar classes. A linha de vazios é um diagnóstico, não uma classe criada no dataset. A soma das classes e dos vazios fecha o total.

## Diagnósticos antes de qualquer limpeza

| Diagnóstico | Resultado |
| --- | ---: |
| Células vazias ou apenas com espaços | 0 |
| Células contendo `NaN` | 4 |
| Linhas com `NaN` | 4 |
| Células contendo `Infinity` | 64 |
| Linhas com pelo menos um infinito | 34 |
| Registros inteiros duplicados, excedentes à primeira ocorrência | 2.633 |
| Registros textualmente distintos | 223.112 |

Distribuição das anomalias numéricas, preservando os cabeçalhos:

| Coluna literal | Posição (base 1) | `NaN` | `Infinity` |
| --- | ---: | ---: | ---: |
| `Flow Bytes/s` | 15 | 4 | 30 |
| ` Flow Packets/s` | 16 | 0 | 34 |

Os valores infinitos encontrados são positivos, escritos literalmente como `Infinity`. Os quatro `NaN` são marcadores explícitos de valor numérico ausente ou indefinido, embora não sejam campos vazios. Os totais de linhas com NaN e com infinito podem se sobrepor e não devem ser somados para obter linhas problemáticas. Os 78 atributos aceitam conversão numérica, incluindo esses valores especiais. A causa dos valores não finitos não foi investigada nesta etapa.

O cabeçalho **` Fwd Header Length` aparece duas vezes**, nas posições 35 e 56. Ambas as colunas foram preservadas e incluídas no total de 79. O dicionário consultado não esclarece a intenção dessa repetição. A análise usa posições para não perder uma delas ao criar um dicionário por nome.

## Procedimento e reprodução

A documentação do CICFlowMeter descreve fluxos bidirecionais. O primeiro pacote define o sentido de ida (origem para destino) e o de volta. A duração é descrita em microssegundos. Os totais de pacotes na ida e na volta são contagens por direção. Esses são os significados usados na explicação da linha.

Fontes dos atributos:

- https://www.unb.ca/cic/research/applications.html
- https://raw.githubusercontent.com/ahlashkari/CICFlowMeter/master/ReadMe.txt

O script `scripts/caracterizar_csv.py` foi executado com **Python 3.12.14**, usando somente a biblioteca padrão: `argparse`, `collections`, `csv`, `hashlib`, `json`, `math`, `platform` e `pathlib`. Não foram usados pandas, NumPy ou outras bibliotecas externas; os módulos padrão acompanham a versão do Python.

Ele lê todos os registros com `csv.reader`, delimitador vírgula, codificação `utf-8-sig`, `newline=''` e `skipinitialspace=False`. Preserva espaços dos cabeçalhos e rótulos, confere a largura de cada registro e rejeita cabeçalhos repetidos. Localiza a coluna cujo nome, após retirar espaços apenas para identificação, é `Label`; o cabeçalho e os valores permanecem intactos. Conta classes sem renomear ou agrupar. Registra separadamente rótulos vazios ou só com espaços, campos vazios, valores convertíveis em NaN e infinitos e campos não numéricos fora da coluna de classe. Mantém zero como valor válido.

Duplicatas são registros com todos os campos textuais iguais, incluindo o rótulo. A contagem é o número de ocorrências excedentes à primeira. Não houve normalização numérica ou textual para essa comparação. São repetições nas características disponíveis no CSV; isso não demonstra que os mesmos eventos de rede foram capturados duas vezes.

Nenhuma linha foi removida, imputada, normalizada ou deduplicada. O CSV extraído mantém os bytes distribuídos. Uma segunda leitura independente das linhas brutas confirmou o total de registros, a distribuição de classes e a quantidade de duplicatas. Os resultados completos, cabeçalhos e exemplos estão em `analise/resultado.json`.

Comando portátil, executado a partir da raiz do projeto com Python 3.12:

```powershell
python scripts/caracterizar_csv.py data/raw/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv --saida analise/resultado.json
```

Comando exato usado neste computador, que não tinha `python` configurado no PATH:

```powershell
& 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe' scripts/caracterizar_csv.py data/raw/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv --saida analise/resultado.json
```

Para extrair o mesmo membro em outro computador, a partir do ZIP obtido pelo cadastro:

```python
from pathlib import Path
from zipfile import ZipFile

nome = 'Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'
with ZipFile('data/raw/MachineLearningCSV.zip') as z:
    conteudo = z.read('MachineLearningCVE/' + nome)
Path('data/raw', nome).write_bytes(conteudo)
```

## Integridade e identificação da cópia

O conteúdo do arquivo oficial `MachineLearningCSV.md5` é:

```text
4f83860afbf29cac8163854095bf6cf7  MachineLearningCVE.zip
```

Embora esse arquivo de checksum mencione `MachineLearningCVE.zip`, o nome disponibilizado na listagem e no download é `MachineLearningCSV.zip`. O MD5 calculado do ZIP baixado corresponde exatamente ao valor publicado. O CRC32 do membro selecionado também foi validado pelo `zipfile` durante a extração.

| Objeto | SHA-256 |
| --- | --- |
| ZIP oficial | `c3f26274b36c837ccf28ffd2dbf4582941c30b3ee70a635c6e5b2f87c4727928` |
| CSV extraído | `6ff1580f5f81c0ae28a26f7631721018577f5f7c5e0feac28b795fcfe7b411ee` |

Os metadados da extração estão em `analise/origem.json`. Para conferir a cópia do colega no PowerShell:

```powershell
Get-FileHash data/raw/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv -Algorithm SHA256
```

## Limites

Esse recorte descreve um cenário de laboratório de um único dia. Não representa toda a semana do CICIDS2017 nem a frequência dos ataques em redes reais. As classes são os rótulos atribuídos pelo dataset.

## Referência

Iman Sharafaldin, Arash Habibi Lashkari e Ali A. Ghorbani. “Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization”. ICISSP, 2018.
