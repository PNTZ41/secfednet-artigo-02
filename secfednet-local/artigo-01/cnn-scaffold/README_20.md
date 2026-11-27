# SCAFFOLD e FedAvg-SGD · 20 rodadas

Extensão do ensaio das 12h37. Mantém suas fontes e saídas intactas e reutiliza o mesmo SGD, cliente, atualização dos controles e agregação. Recomeça dos mesmos pesos iniciais, executa vinte rodadas completas e confere que as duas primeiras reproduzem os pesos, controles e scores do piloto. Não há early stopping.

Da raiz do repositório, com destino novo:

```bash
bash secfednet-local/artigo-01/cnn-scaffold/reproduzir_20.sh secfednet-local/artigo-01/cnn-scaffold/reproducao-20
```

O ambiente é `../cnn-flower/.venv`, fixado por [requirements.lock](../cnn-flower/requirements.lock), já validado em Linux x86-64, CPython 3.14.4, PyTorch 2.12.1+cpu, Flower 1.32.0 e NumPy 2.3.5. O wrapper não instala dependências. Rode `sha256sum -c secfednet-local/artigo-01/cnn-scaffold/SHA256_FONTES_20` da raiz para conferir as fontes e referências.

## Configuração fixa

[protocolo_20.json](protocolo_20.json): 20 rodadas, cinco clientes participantes, uma época local, lote 512, SGD lr=0,01 sem momentum/decay, média uniforme dos modelos e taxa global 1 em ambos os métodos. Seeds: modelo 23, partição Dirichlet α=0,5 com seed 2305, minibatches `23+100*rodada+cliente`. A mesma função de atualização SCAFFOLD opção II e os controles persistentes do piloto são usados sem modificação.

Manifesto da validação das 09h04: SHA-256 `bb710d6492ac83456b61ba8469d06f6729bf063ba586a557b0165a701173339f`. Ajuste: 203.251 exemplos; validação: 50.815 (40.776 BENIGN e 10.039 DDoS). Os índices, grupos e vetores float32 são reconferidos. Normalização só no ajuste; mesmas 81 features em ordem, sem metadados. Contrato completo em `execucao/configuracao.json` e nos checkpoints. O teste cronológico global não é inferido.

Cada rodada registra BCE do modelo global após agregação: média por exemplos e média uniforme das cinco médias por cliente. Registra separadamente a BCE online durante os passos locais, também nas duas ponderações. Inferências de monitoramento não fazem passos de gradiente. Nenhuma decisão de treinamento depende da curva.

Na validação, escolhe o limiar que maximiza recall DDoS com FPR≤1%, desempate por menor FP e maior limiar; `score>=limiar`. Há no máximo 407 FP, respeitando empates de score. O score é sigmoide do logit DDoS, sem calibração probabilística. A mesma validação escolhe o limiar e mede desempenho: resultado exploratório.

## Orçamentos e comparações

Por rodada: 400 passos e 203.251 exposições em ambos os métodos. Parâmetros: 45.960 bytes agregando cinco clientes e os dois sentidos. SCAFFOLD acrescenta 45.960 bytes de controles. São arrays float32 brutos da simulação em processo; não incluem serialização, metadados, rede ou disco.

- Rodada 20 contra rodada 20: mesmos 8.000 passos e 4.065.020 exposições por método; 919.200 bytes em FedAvg e 1.838.400 em SCAFFOLD.
- FedAvg 20 contra SCAFFOLD 10: mesmos 919.200 bytes brutos; SCAFFOLD usa 4.000 passos e 2.032.510 exposições, metade do orçamento de gradiente de FedAvg.

Os dois pontos são fixados antes de avaliar. A tabela final não escolhe a melhor rodada observada.

## Saídas e conferência

A execução registrada é `ensaio-20-rodadas/`. Em cada nova saída:

- `teste_controles/`: teste manual de duas rodadas, com retomada em outro processo.
- `execucao/configuracao.json`, `clientes.npz`, `pesos_iniciais.pt`: configuração antes do treino e referências de pareamento.
- `execucao/{fedavg_sgd,scaffold}/curva.json` e `curva.csv`: 20 pontos com perdas, recall, FPR, FP, limiar, macro-F1, bytes, passos e exposições acumuladas.
- `execucao/curvas.csv`: 40 pontos dos dois métodos para plotagem.
- `execucao/{fedavg_sgd,scaffold}/rodada-00.pt` até `rodada-20.pt`: pesos e todos os controles; `scores_validacao_01.npy` até `scores_validacao_20.npy`: scores por rodada.
- `execucao/{fedavg_sgd,scaffold}/treino.json`, `rodadas.json`, `checkpoint.pt`: instrumentação, tempo e modelo final com normalização/contrato.
- `execucao/comparacoes.json`, `resultados.json`, `pareamento.json`, `verificacao_independente.json`, `tempo.json`.
- Logs sanitizados de treino, teste dos controles e verificação em outro processo ao lado de `execucao/`.

O processo separado recarrega os 40 estados com `weights_only=True`, reproduz scores bit a bit e reconfere as métricas e o suporte. Também verifica os dois checkpoints finais. A mesma recarga usa apenas validação interna.

O inventário atualizado está em [PRIMEIRO_COMMIT.md](../cnn-validacao/PRIMEIRO_COMMIT.md). As fontes ainda estão em pasta ignorada. Nenhum commit é feito por estes comandos.
