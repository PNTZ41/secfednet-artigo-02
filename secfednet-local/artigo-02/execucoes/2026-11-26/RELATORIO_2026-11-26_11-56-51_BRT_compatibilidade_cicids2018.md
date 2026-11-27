# Artigo 02 · Compatibilidade do CSE-CIC-IDS2018 corrigido com a CNN

26/11/2026, 11:56:51, Belém (UTC−03). Objetivo: conferir se os CSVs corrigidos de 20 e 21 de fevereiro de 2018 podem alimentar o FedAvg limpo usado no SecFedNet.

**Resultado.** Compatibilidade estrutural confirmada nos dois cabeçalhos oficiais. Ambos têm 91 colunas com nomes únicos. As posições 9–89 correspondem exatamente aos 81 atributos do contrato, na mesma ordem, sem renomeação. Nenhum atributo está ausente. A equivalência numérica das duas extrações ainda é parcial. A amostra não qualifica o checkpoint para inferência de produção nem confirma a generalização do modelo. [Contrato da CNN](../../../../integracao/artigo-01/contrato-cnn/contrato.json) · [Proposta de avaliação](RELATORIO_2026-11-26_11-39-50_BRT_avaliacao_fedavg_limpo.md).

## Evidência direta e proveniência

Consultei a distribuição corrigida de Liu et al. (IEEE CNS 2022), o notebook de rotulagem e o fork do extrator dos autores. A página do CIC/UNB identifica a coleta original. Os cabeçalhos abaixo vêm do ZIP corrigido e os resultados do notebook são da rotulagem corrigida. A versão original do CIC/UNB não serve para substituir cabeçalhos, contagens ou rótulos da edição corrigida. [Distribuição CNS2022](https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/) · [Documentação da coleta original](https://www.unb.ca/cic/datasets/ids-2018.html) · [Documentação da correção](https://intrusion-detection.distrinet-research.be/CNS2022/CSECICIDS2018.html).

O servidor retornou ETag `"26d7d2191-5f86fb8b66b7b"` e 10.426.851.729 bytes. Li 9.416 bytes por HTTP Range, incluindo diretório ZIP, cabeçalho local dos membros e os primeiros 4.096 bytes Deflate de cada membro. A leitura produziu os dois cabeçalhos e 22 registros completos iniciais. O CRC32 abaixo vem do diretório ZIP. A leitura parcial não recalcula CRC32 nem SHA-256 do membro inteiro. Registrei cabeçalhos e contagens de rótulos da amostra, sem guardar linhas de tráfego. [Evidência direta em JSON](EVIDENCIA_2026-11-26_cicids2018_cabecalhos.json).

| Membro | Tamanho descompactado | CRC32 do diretório | Linhas completas examinadas |
|---|---:|---|---:|
| `Tuesday-20-02-2018.csv` | 3.431.246.090 B | `e0a48bbb` | 12 BENIGN, todas categoria −1 |
| `Wednesday-21-02-2018.csv` | 3.952.691.068 B | `d485a089` | 10 BENIGN, todas categoria −1 |

## Mapeamento dos 81 atributos

**C** significa cabeçalho observado nos dois CSVs e definição confirmada no código de referência consultado. **P** significa cabeçalho observado e cálculo de referência identificado, com checagem específica pendente nas duas exportações. **A** seria ausência no cabeçalho. São 55 C, 26 P e 0 A. Para todas as linhas, a identificação do binário ou commit exato que gerou cada edição continua pendente. C indica confirmação documental da regra, sem certificar paridade numérica das duas edições ou todos os casos de borda.

A coluna pelo nome coincide com o atributo da CNN. A posição é base 1 em ambos os CSVs. B significa byte e IAT é o intervalo entre pacotes sucessivos. Fwd/Bwd são os sentidos do fluxo no extrator. O código pode preservar o sentido entre segmentos ou invertê-lo quando identifica um SYN-ACK inicial. Os comprimentos de pacote nesta tabela vêm de payload. As estatísticas usam `SummaryStatistics` (desvio e variância amostrais). O serializador de referência usa zero em estatísticas sem direção ou sem intervalos suficientes, segundo a regra de cada grupo. Os bulks acumulam pelo menos quatro pacotes com payload, com intervalo de até 1 s na mesma direção e reinício conforme a atividade do sentido oposto. Os subfluxos usam o contador de lacunas acima de 1 s, com possíveis conversões na exportação. [Alterações do extrator](https://intrusion-detection.distrinet-research.be/CNS2022/Tools_Documentation.html) · [Cálculos e serialização](https://github.com/GintsEngelen/CICFlowMeter/blob/master/src/main/java/cic/cs/unb/ca/jnetpcap/BasicFlow.java) · [Formação e término de fluxos](https://github.com/GintsEngelen/CICFlowMeter/blob/master/src/main/java/cic/cs/unb/ca/jnetpcap/FlowGenerator.java) · [Campos de pacote](https://github.com/GintsEngelen/CICFlowMeter/blob/master/src/main/java/cic/cs/unb/ca/jnetpcap/BasicPacketInfo.java).

| Nº CNN | Atributo CNN e nome da coluna em ambos os CSVs | Posição CSV | Unidade | Regra no extrator de referência | Estado |
|---:|---|---:|---|---|---|
| 1 | `Flow Duration` | 9 | µs | Tempo do último pacote menos tempo do primeiro. | C |
| 2 | `Total Fwd Packet` | 10 | pacotes | Contagem de pacotes Fwd. | C |
| 3 | `Total Bwd packets` | 11 | pacotes | Contagem de pacotes Bwd. | C |
| 4 | `Total Length of Fwd Packet` | 12 | B | Soma dos bytes de payload Fwd. | C |
| 5 | `Total Length of Bwd Packet` | 13 | B | Soma dos bytes de payload Bwd. | C |
| 6 | `Fwd Packet Length Max` | 14 | B | Máximo do tamanho do payload por pacote Fwd. | C |
| 7 | `Fwd Packet Length Min` | 15 | B | Mínimo do tamanho do payload por pacote Fwd. | C |
| 8 | `Fwd Packet Length Mean` | 16 | B | Média do tamanho do payload por pacote Fwd. | C |
| 9 | `Fwd Packet Length Std` | 17 | B | Desvio amostral do tamanho do payload por pacote Fwd. | C |
| 10 | `Bwd Packet Length Max` | 18 | B | Máximo do tamanho do payload por pacote Bwd. | C |
| 11 | `Bwd Packet Length Min` | 19 | B | Mínimo do tamanho do payload por pacote Bwd. | C |
| 12 | `Bwd Packet Length Mean` | 20 | B | Média do tamanho do payload por pacote Bwd. | C |
| 13 | `Bwd Packet Length Std` | 21 | B | Desvio amostral do tamanho do payload por pacote Bwd. | C |
| 14 | `Flow Bytes/s` | 22 | B/s | Soma de bytes de payload nas duas direções dividida pela duração em segundos. O exportador de referência emite −1 para duração zero. | P |
| 15 | `Flow Packets/s` | 23 | pacotes/s | Contagem total de pacotes dividida pela duração em segundos. O exportador de referência emite −1 para duração zero. | P |
| 16 | `Flow IAT Mean` | 24 | µs | Média das diferenças entre timestamps consecutivos do fluxo, nas duas direções. | C |
| 17 | `Flow IAT Std` | 25 | µs | Desvio amostral das diferenças entre timestamps consecutivos do fluxo, nas duas direções. | C |
| 18 | `Flow IAT Max` | 26 | µs | Máximo das diferenças entre timestamps consecutivos do fluxo, nas duas direções. | C |
| 19 | `Flow IAT Min` | 27 | µs | Mínimo das diferenças entre timestamps consecutivos do fluxo, nas duas direções. | C |
| 20 | `Fwd IAT Total` | 28 | µs | Soma das diferenças entre timestamps consecutivos na direção Fwd. | C |
| 21 | `Fwd IAT Mean` | 29 | µs | Média das diferenças entre timestamps consecutivos na direção Fwd. | C |
| 22 | `Fwd IAT Std` | 30 | µs | Desvio amostral das diferenças entre timestamps consecutivos na direção Fwd. | C |
| 23 | `Fwd IAT Max` | 31 | µs | Máximo das diferenças entre timestamps consecutivos na direção Fwd. | C |
| 24 | `Fwd IAT Min` | 32 | µs | Mínimo das diferenças entre timestamps consecutivos na direção Fwd. | C |
| 25 | `Bwd IAT Total` | 33 | µs | Soma das diferenças entre timestamps consecutivos na direção Bwd. | C |
| 26 | `Bwd IAT Mean` | 34 | µs | Média das diferenças entre timestamps consecutivos na direção Bwd. | C |
| 27 | `Bwd IAT Std` | 35 | µs | Desvio amostral das diferenças entre timestamps consecutivos na direção Bwd. | C |
| 28 | `Bwd IAT Max` | 36 | µs | Máximo das diferenças entre timestamps consecutivos na direção Bwd. | C |
| 29 | `Bwd IAT Min` | 37 | µs | Mínimo das diferenças entre timestamps consecutivos na direção Bwd. | C |
| 30 | `Fwd PSH Flags` | 38 | pacotes | Contagem de pacotes Fwd com flag TCP PSH. | C |
| 31 | `Bwd PSH Flags` | 39 | pacotes | Contagem de pacotes Bwd com flag TCP PSH. | C |
| 32 | `Fwd URG Flags` | 40 | pacotes | Contagem de pacotes Fwd com flag TCP URG. | C |
| 33 | `Bwd URG Flags` | 41 | pacotes | Contagem de pacotes Bwd com flag TCP URG. | C |
| 34 | `Fwd RST Flags` | 42 | pacotes | Contagem de pacotes Fwd com flag TCP RST. | C |
| 35 | `Bwd RST Flags` | 43 | pacotes | Contagem de pacotes Bwd com flag TCP RST. | C |
| 36 | `Fwd Header Length` | 44 | B | Soma dos bytes de cabeçalho reportados pelo extrator por pacote Fwd. Notebook converte para int16. | P |
| 37 | `Bwd Header Length` | 45 | B | Soma dos bytes de cabeçalho reportados pelo extrator por pacote Bwd. Notebook converte para int16. | P |
| 38 | `Fwd Packets/s` | 46 | pacotes/s | Contagem Fwd dividida pela duração do fluxo em segundos, ou zero se a duração não for positiva. | C |
| 39 | `Bwd Packets/s` | 47 | pacotes/s | Contagem Bwd dividida pela duração do fluxo em segundos, ou zero se a duração não for positiva. | C |
| 40 | `Packet Length Min` | 48 | B | Mínimo do tamanho do payload por pacote, nas duas direções. | C |
| 41 | `Packet Length Max` | 49 | B | Máximo do tamanho do payload por pacote, nas duas direções. | C |
| 42 | `Packet Length Mean` | 50 | B | Média do tamanho do payload por pacote, nas duas direções. | C |
| 43 | `Packet Length Std` | 51 | B | Desvio amostral do tamanho do payload por pacote, nas duas direções. | C |
| 44 | `Packet Length Variance` | 52 | B² | Variância amostral do tamanho do payload por pacote, nas duas direções. | C |
| 45 | `FIN Flag Count` | 53 | pacotes | Contagem de pacotes com flag TCP FIN nas duas direções. | C |
| 46 | `SYN Flag Count` | 54 | pacotes | Contagem de pacotes com flag TCP SYN nas duas direções. | C |
| 47 | `RST Flag Count` | 55 | pacotes | Contagem de pacotes com flag TCP RST nas duas direções. | C |
| 48 | `PSH Flag Count` | 56 | pacotes | Contagem de pacotes com flag TCP PSH nas duas direções. | C |
| 49 | `ACK Flag Count` | 57 | pacotes | Contagem de pacotes com flag TCP ACK nas duas direções. | C |
| 50 | `URG Flag Count` | 58 | pacotes | Contagem de pacotes com flag TCP URG nas duas direções. | C |
| 51 | `CWR Flag Count` | 59 | pacotes | Contagem de pacotes com flag TCP CWR nas duas direções. | C |
| 52 | `ECE Flag Count` | 60 | pacotes | Contagem de pacotes com flag TCP ECE nas duas direções. | C |
| 53 | `Down/Up Ratio` | 61 | razão | Contagem Bwd dividida pela Fwd, em ponto flutuante, ou zero sem pacotes Fwd. | C |
| 54 | `Average Packet Size` | 62 | B/pacote | Soma de comprimentos de payload nas duas direções dividida pelo número de pacotes. | C |
| 55 | `Fwd Segment Size Avg` | 63 | B/pacote | Soma dos bytes de payload Fwd dividida pelo número de pacotes Fwd. | C |
| 56 | `Bwd Segment Size Avg` | 64 | B/pacote | Soma dos bytes de payload Bwd dividida pelo número de pacotes Bwd. | C |
| 57 | `Fwd Bytes/Bulk Avg` | 65 | B/bulk | Bytes de payload Fwd em bulks divididos pelo número de bulks. | P |
| 58 | `Fwd Packet/Bulk Avg` | 66 | pacotes/bulk | Pacotes Fwd em bulks divididos pelo número de bulks. | P |
| 59 | `Fwd Bulk Rate Avg` | 67 | B/s | Bytes de payload Fwd em bulks divididos pela soma das durações dos bulks em segundos. | P |
| 60 | `Bwd Bytes/Bulk Avg` | 68 | B/bulk | Bytes de payload Bwd em bulks divididos pelo número de bulks. | P |
| 61 | `Bwd Packet/Bulk Avg` | 69 | pacotes/bulk | Pacotes Bwd em bulks divididos pelo número de bulks. | P |
| 62 | `Bwd Bulk Rate Avg` | 70 | B/s | Bytes de payload Bwd em bulks divididos pela soma das durações dos bulks em segundos. | P |
| 63 | `Subflow Fwd Packets` | 71 | pacotes/subfluxo | Total de pacotes Fwd dividido pelo contador de subfluxos do extrator, ou zero se contador zero. Conferir conversão int32. | P |
| 64 | `Subflow Fwd Bytes` | 72 | B/subfluxo | Bytes de payload Fwd divididos pelo contador de subfluxos, ou zero se contador zero. Conferir conversão int32. | P |
| 65 | `Subflow Bwd Packets` | 73 | pacotes/subfluxo | Total de pacotes Bwd dividido pelo contador de subfluxos do extrator, ou zero se contador zero. Conferir conversão int32. | P |
| 66 | `Subflow Bwd Bytes` | 74 | B/subfluxo | Bytes de payload Bwd divididos pelo contador de subfluxos, ou zero se contador zero. Conferir conversão int32. | P |
| 67 | `FWD Init Win Bytes` | 75 | B | Valor bruto da janela TCP no primeiro pacote Fwd quando ele inicia o fluxo. Em casos de inversão inicial, conferir o valor emitido. | P |
| 68 | `Bwd Init Win Bytes` | 76 | B | Janela TCP do lado Bwd. O código de referência volta a atualizar enquanto o valor armazenado é zero. | P |
| 69 | `Fwd Act Data Pkts` | 77 | pacotes | Contagem Fwd de pacotes com payload de pelo menos 1 B. | C |
| 70 | `Fwd Seg Size Min` | 78 | B | Menor comprimento de cabeçalho fornecido ao extrator na direção Fwd, sujeito à inicialização do sentido. | P |
| 71 | `Active Mean` | 79 | µs | Média das durações ativas entre pausas. Conferir tratamento do último trecho. | P |
| 72 | `Active Std` | 80 | µs | Desvio amostral das durações ativas entre pausas. Conferir tratamento do último trecho. | P |
| 73 | `Active Max` | 81 | µs | Máximo das durações ativas entre pausas. Conferir tratamento do último trecho. | P |
| 74 | `Active Min` | 82 | µs | Mínimo das durações ativas entre pausas. Conferir tratamento do último trecho. | P |
| 75 | `Idle Mean` | 83 | µs | Média dos intervalos ociosos entre trechos ativos. Conferir tratamento do último trecho. | P |
| 76 | `Idle Std` | 84 | µs | Desvio amostral dos intervalos ociosos entre trechos ativos. Conferir tratamento do último trecho. | P |
| 77 | `Idle Max` | 85 | µs | Máximo dos intervalos ociosos entre trechos ativos. Conferir tratamento do último trecho. | P |
| 78 | `Idle Min` | 86 | µs | Mínimo dos intervalos ociosos entre trechos ativos. Conferir tratamento do último trecho. | P |
| 79 | `ICMP Code` | 87 | código inteiro | Campo Code copiado do primeiro pacote do fluxo ICMP, com sentinela −1 quando indisponível no código de referência. | C |
| 80 | `ICMP Type` | 88 | tipo inteiro | Campo Type copiado do primeiro pacote do fluxo ICMP, com sentinela −1 quando indisponível no código de referência. | C |
| 81 | `Total TCP Flow Time` | 89 | µs | Duração acumulada de fluxos da mesma conexão, incluindo intervalos entre segmentos quando o estado é herdado. Confirmar protocolos, condições de término e acumulação na revisão do ZIP. | P |

Os pontos P pedem comparação das duas revisões e de vetores conhecidos. O notebook converte cabeçalhos para inteiros de 16 bits e subfluxos para inteiros de 32 bits. Conferir overflow em cabeçalhos e truncamento em subfluxos. Conferir valores sentinela, sentido em fluxos vazios, fechamento dos períodos Active/Idle e o estado acumulado de `Total TCP Flow Time`. O código consultado trata TCP e UDP no acumulador, apesar do nome da coluna. A revisão pública também serializa campos extras que não aparecem nos cabeçalhos observados. Isso torna necessário vincular cada CSV ao binário ou commit usado para produzi-lo. [Notebook dos autores](https://github.com/GintsEngelen/CNS2022_Code/blob/main/Labelling/CICIDS2018_labelling_fixed_CICFlowMeter.ipynb) · [Serialização do extrator](https://github.com/GintsEngelen/CICFlowMeter/blob/master/src/main/java/cic/cs/unb/ca/jnetpcap/BasicFlow.java#L1166).

## Sessões e suporte por classe

O cabeçalho confirma `id`, `Flow ID`, IP e porta de origem e destino, `Protocol` e `Timestamp`. O extrator documenta UTC com precisão de microssegundos. Usar `Timestamp` como início e derivar término com `Flow Duration`, após conferir a unidade e o parsing. `id` é índice local do CSV. `Flow ID` incorpora os endpoints e o protocolo e pode repetir em janelas distintas. Usar arquivo/origem e número de linha para identidade de registro. Para detectar eventos duplicados e agrupar sessões, combinar quíntupla bidirecional, janela temporal, origem da captura e regra de continuidade. O cabeçalho carece de identificador de campanha, sessão, sensor ou PCAP de origem.

Na documentação corrigida, o dia 20 registra LOIC HTTP e UDP e o dia 21 registra LOIC UDP e HOIC. São quatro janelas de rotulagem, com compartilhamento de infraestrutura entre dias. Um corte por data é uma hipótese de separação temporal. Para confirmá-lo, auditar fluxos que atravessam a fronteira, continuidades da mesma conexão, reexportações e vetores coincidentes. As janelas de DDoS não definem sessões BENIGN. Para atribuição de metadados, o notebook usa horário e endpoints. Em divergências entre texto e código (por exemplo, o destino publicado para o LOIC UDP de 21/02), preservar os rótulos do CSV e pedir a revisão efetivamente usada. Separar os dias também altera famílias e prevalência. [Documentação corrigida](https://intrusion-detection.distrinet-research.be/CNS2022/CSECICIDS2018.html#loic) · [Código de rotulagem e saídas por dia](https://raw.githubusercontent.com/GintsEngelen/CNS2022_Code/main/Labelling/CICIDS2018_labelling_fixed_CICFlowMeter.ipynb#L339).

| Dia | BENIGN publicado | DDoS publicado, sem Attempted | Attempted publicado | Total publicado |
|---|---:|---:|---:|---:|
| 20/02 | 5.764.497 | 290.125 (289.328 LOIC HTTP + 797 LOIC UDP) | 80 | 6.054.702 |
| 21/02 | 5.878.399 | 1.084.023 (1.082.293 HOIC + 1.730 LOIC UDP) | 171 | 6.962.593 |

As contagens acima constam na saída publicada do notebook. Em cada dia, BENIGN + DDoS sem Attempted fecha com a contagem de categoria −1 publicada. O site documenta correções posteriores ao lançamento inicial. A vinculação dessas saídas ao CRC32 dos arquivos distribuídos e a contagem por sessão após os filtros do Artigo 02 permanecem pendentes. A confirmação direta desta missão é de 12 e 10 BENIGN no prefixo, respectivamente, sem DDoS observado nesse prefixo. Mapear somente os três rótulos DDoS documentados para classe 1 e BENIGN para 0, mantendo Attempted em contagem separada (categoria diferente de −1 ou sufixo Attempted) e registrando outros rótulos. [Saída do notebook, 20/02](https://raw.githubusercontent.com/GintsEngelen/CNS2022_Code/main/Labelling/CICIDS2018_labelling_fixed_CICFlowMeter.ipynb#L339) · [Saída do notebook, 21/02](https://raw.githubusercontent.com/GintsEngelen/CNS2022_Code/main/Labelling/CICIDS2018_labelling_fixed_CICFlowMeter.ipynb#L407) · [Orientação sobre Attempted](https://intrusion-detection.distrinet-research.be/CNS2022/Dataset_Download.html).

## Parecer sobre o checkpoint e menor insumo restante

**O checkpoint da rodada 20 é candidato a um ensaio de transferência com pesos congelados**, condicionado à validação numérica do pré-processamento. O relatório histórico mede validação interna do CICIDS2017. A compatibilidade do formato não garante recall, FPR ou validade do limiar de 0,365106 no novo domínio. Usar os 81 valores brutos e o normalizador original do checkpoint. O teste de transferência requer o artefato da rodada 20 com seu hash, metadados e normalizador. O ZIP de inferência de três rodadas é outro modelo. O checkout consultado tem as referências do ensaio, sem binários `.pt` disponíveis. Calibrar o limiar somente em sessões de calibração. Fixá-lo antes da avaliação e reportar o resultado como transferência entre domínios. Um estudo com ajuste de pesos no CSE-CIC-IDS2018 constitui outro experimento. A sexta do CICIDS2017 permanece reservada. [Condições do ensaio de 20 rodadas](../../../artigo-01/cnn-scaffold/README_20.md) · [Contrato e distinção entre os checkpoints](../../../../integracao/artigo-01/contrato-cnn/CONTRATO.md).

O menor pacote de evidência que falta independe do ZIP completo:

1. **Paridade numérica.** Identidade do binário ou commit, parâmetros e versões para as duas extrações (2017 corrigido usado no treino e 2018 corrigido). Juntar uma pequena amostra de referência do mesmo conjunto de pacotes processado pelos dois extratores, com vetores esperados para TCP, UDP e ICMP, casos com duração zero, mudanças de sentido, bulk, subfluxo e conexões partidas pelo timeout. A amostra pode ser um teste sintético de parser ou médias e valores esperados fornecidos pelos autores. Incluir os casos de conversão de inteiros. Cabeçalhos adicionais já são dispensáveis.
2. **Suporte e separação.** Um manifesto compactado, vinculado ao hash de cada membro, com contagens por rótulo bruto, Attempted e pós-filtros, por sessão e origem; IDs ou hashes de eventos e sessões, limites UTC e informação de PCAP/campanha. Incluir contagens de interseções por evento e vetor antes/depois de normalizar para float32. Esses agregados podem ser gerados por quem já possui os CSVs. Se for necessário recalcular a separação, a menor entrega útil é a projeção dos campos de identidade, rótulo e tempo, mais hashes das representações. Os totais isolados não auditam fronteiras.
3. **Execução futura.** Para inferência, obter o checkpoint exato e os dois subconjuntos com as 81 colunas e rótulos, selecionados por manifesto. Confirmar suporte em ambos antes de medir desempenho. Essa etapa vem depois do parecer de compatibilidade.

## Registro de execução

Branch inicial/final `integracao/artigo-01` em `4cc2727`. Estado visível inicial/final: `secfednet-local/artigo-01/INDEX.md` já modificado e `.idea/` já não rastreada. Sob `secfednet-local/artigo-02/` foram escritos o relatório, a evidência JSON, o índice e o status. O helper da leitura está em `/tmp/secfednet_zip_headers.py`, fora do repositório. Instrução local `AGENTS.md`. `.agents/` e `.codex/` vazios. Nenhum arquivo da sexta foi consultado nesta missão. Sem treino ou inferência.

Comandos de conferência: `git status`, `git rev-parse`, `rg`, `cat`, `ls`, `TZ=America/Belem date`, `curl -fsSI` para metadados HTTP e `python3 -B /tmp/secfednet_zip_headers.py` para a leitura parcial. O helper abre o ZIP remotamente por seek, exige HTTP 206, valida Content-Range, fixa ETag por If-Match e limita a leitura a 512 KiB. A comparação local usa apenas a evidência armazenada. Da raiz:

```sh
python3 -B - <<'PY'
import json
from pathlib import Path
contrato = json.loads(Path("integracao/artigo-01/contrato-cnn/contrato.json").read_text())
evidencia = json.loads(Path("secfednet-local/artigo-02/execucoes/2026-11-26/EVIDENCIA_2026-11-26_cicids2018_cabecalhos.json").read_text())
for membro in evidencia["members"]:
    h = membro["header"]
    assert len(h) == len(set(h)) == 91 and len(contrato["ordem_features"]) == 81
    assert h[8:89] == contrato["ordem_features"]
    assert h[-2:] == ["Label", "Attempted Category"]
    print(membro["member"], "81/81", membro["prefix_counts"])
PY
```
