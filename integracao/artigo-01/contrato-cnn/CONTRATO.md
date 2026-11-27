# Contrato de inferência CNN-1D v1

Checkpoint `checkpoint_cnn1d.pt` no ZIP separado `secfednet-cnn1d-v1.zip`.
SHA-256 do checkpoint: `37db7d4f6d0123786cc4ed5227d670edb1344c07089e8ff6910c6446e57400f3`. SHA-256 do ZIP: `e7d042b38c77b96bef54533302bef817d6b8a4a8e55b717bac7b32f98b5b6014`.
Modelo original FedAvg, três rodadas em CPU com cinco clientes, Adam lr=0,001; treino final de 254.074 fluxos. O ZIP foi preservado integralmente. Os checkpoints dos ensaios SGD/SCAFFOLD são outros artefatos.

Entrada obrigatória: objeto JSON com `features`, lista de **81 números finitos brutos**, na ordem abaixo. Booleanos e lista com outra largura são rejeitados. Metadados do exemplo, como `rotulo_real`, não entram no modelo. Identificadores e timestamp não fazem parte das features.

O preditor usa a média e o desvio ddof=0 salvos no checkpoint, ajustados somente no treino; escala zero vira 1. Faz `(x-media)/escala` em float64 e converte para float32 para a CNN. A equipe consumidora fornece valores brutos, sem aplicar novamente essa normalização.

| Campo da saída | Significado |
| --- | --- |
| `classe_id` | 0=BENIGN, 1=DDoS. Predição com limiar **0,5**, incluindo a igualdade em DDoS. |
| `classe` | Nome correspondente ao identificador previsto; não é o rótulo real do exemplo. |
| `score` | Sigmoide do logit para DDoS, em [0,1], sem calibração probabilística. Sempre se refere a DDoS, inclusive quando a classe prevista é BENIGN. |
| `embedding` | 16 ativações da camada `embedding.1` (ReLU da linear 48→16), antes da cabeça de classificação. Não são probabilidades nem vetor normalizado; a ordem das coordenadas é fixa para este checkpoint. |

O limiar 0,5 do pacote é fixo. Os limiares exploratórios calibrados na validação dos ensaios posteriores pertencem àqueles checkpoints; esta entrega mantém o contrato do ZIP original. O teto empírico de FPR de 1% desses ensaios não é um compromisso do pacote de inferência.

Exemplo real: [entrada completa](exemplo_entrada.json), com rótulo auxiliar DDoS. Resultado: `classe_id=1`, `classe=DDoS`, `score=0.987495481967926`, embedding de 16 valores. [Saída completa](exemplo_saida.json), [contrato JSON](contrato.json), [identidade do pacote](pacote_inferencia.json).

## Ordem das features, posição base 1

Preserve a ordem e a grafia. Este esquema é o CICIDS2017 corrigido; o piloto histórico de Gabriel usava 78 features.

| Posição | Cabeçalho literal |
| --- | --- |
| 1 | `Flow Duration` |
| 2 | `Total Fwd Packet` |
| 3 | `Total Bwd packets` |
| 4 | `Total Length of Fwd Packet` |
| 5 | `Total Length of Bwd Packet` |
| 6 | `Fwd Packet Length Max` |
| 7 | `Fwd Packet Length Min` |
| 8 | `Fwd Packet Length Mean` |
| 9 | `Fwd Packet Length Std` |
| 10 | `Bwd Packet Length Max` |
| 11 | `Bwd Packet Length Min` |
| 12 | `Bwd Packet Length Mean` |
| 13 | `Bwd Packet Length Std` |
| 14 | `Flow Bytes/s` |
| 15 | `Flow Packets/s` |
| 16 | `Flow IAT Mean` |
| 17 | `Flow IAT Std` |
| 18 | `Flow IAT Max` |
| 19 | `Flow IAT Min` |
| 20 | `Fwd IAT Total` |
| 21 | `Fwd IAT Mean` |
| 22 | `Fwd IAT Std` |
| 23 | `Fwd IAT Max` |
| 24 | `Fwd IAT Min` |
| 25 | `Bwd IAT Total` |
| 26 | `Bwd IAT Mean` |
| 27 | `Bwd IAT Std` |
| 28 | `Bwd IAT Max` |
| 29 | `Bwd IAT Min` |
| 30 | `Fwd PSH Flags` |
| 31 | `Bwd PSH Flags` |
| 32 | `Fwd URG Flags` |
| 33 | `Bwd URG Flags` |
| 34 | `Fwd RST Flags` |
| 35 | `Bwd RST Flags` |
| 36 | `Fwd Header Length` |
| 37 | `Bwd Header Length` |
| 38 | `Fwd Packets/s` |
| 39 | `Bwd Packets/s` |
| 40 | `Packet Length Min` |
| 41 | `Packet Length Max` |
| 42 | `Packet Length Mean` |
| 43 | `Packet Length Std` |
| 44 | `Packet Length Variance` |
| 45 | `FIN Flag Count` |
| 46 | `SYN Flag Count` |
| 47 | `RST Flag Count` |
| 48 | `PSH Flag Count` |
| 49 | `ACK Flag Count` |
| 50 | `URG Flag Count` |
| 51 | `CWR Flag Count` |
| 52 | `ECE Flag Count` |
| 53 | `Down/Up Ratio` |
| 54 | `Average Packet Size` |
| 55 | `Fwd Segment Size Avg` |
| 56 | `Bwd Segment Size Avg` |
| 57 | `Fwd Bytes/Bulk Avg` |
| 58 | `Fwd Packet/Bulk Avg` |
| 59 | `Fwd Bulk Rate Avg` |
| 60 | `Bwd Bytes/Bulk Avg` |
| 61 | `Bwd Packet/Bulk Avg` |
| 62 | `Bwd Bulk Rate Avg` |
| 63 | `Subflow Fwd Packets` |
| 64 | `Subflow Fwd Bytes` |
| 65 | `Subflow Bwd Packets` |
| 66 | `Subflow Bwd Bytes` |
| 67 | `FWD Init Win Bytes` |
| 68 | `Bwd Init Win Bytes` |
| 69 | `Fwd Act Data Pkts` |
| 70 | `Fwd Seg Size Min` |
| 71 | `Active Mean` |
| 72 | `Active Std` |
| 73 | `Active Max` |
| 74 | `Active Min` |
| 75 | `Idle Mean` |
| 76 | `Idle Std` |
| 77 | `Idle Max` |
| 78 | `Idle Min` |
| 79 | `ICMP Code` |
| 80 | `ICMP Type` |
| 81 | `Total TCP Flow Time` |
