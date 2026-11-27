# Piloto SCAFFOLD · Artigo 01

Execução curta, somente na validação interna congelada das 09h04. Preserva todos os pilotos e o pacote de inferência. A CNN e o pré-processamento são importados dos scripts existentes.

Da raiz do repositório, com uma pasta de saída ainda inexistente:

```bash
bash secfednet-local/artigo-01/cnn-scaffold/reproduzir.sh secfednet-local/artigo-01/cnn-scaffold/reproducao-02
```

O comando executa o teste escalar de duas rodadas, treina os dois métodos e recarrega os checkpoints em outro processo. O ambiente é `../cnn-flower/.venv`, com dependências fixadas em [requirements.lock](../cnn-flower/requirements.lock). Não instala pacotes. O lock já foi validado em Linux x86-64, CPython 3.14.4; as versões efetivamente usadas estão em `execucao/configuracao.json`.

## Protocolo

[protocolo.json](protocolo.json) é fixado antes de treinar. Dois métodos do zero, duas rodadas, cinco clientes com participação completa, uma época local, lote 512, SGD com lr=0,01, sem momentum e sem weight decay. Seeds: modelo 23, Dirichlet α=0,5 com seed 2305, minibatches `23 + 100*rodada + cliente`. Mesmas partições e ordens da execução das 09h04, verificadas por hash. A agregação dos modelos é uniforme por cliente nos dois métodos, com taxa global 1. Isso difere da média ponderada e do Adam do piloto anterior; a comparação aqui é com um FedAvg-SGD novo.

A [opção II do SCAFFOLD](https://proceedings.mlr.press/v119/karimireddy20a/karimireddy20a.pdf) usa, para cada cliente, referências fixas ao modelo global `x`, ao controle global `c` e ao controle local anterior `ci` durante a rodada:

```text
y <- y - lr * (gradiente_BCE(y) - ci + c)
ci_novo <- ci - c + (x-y)/(K_i*lr)
c <- c + soma(ci_novo-ci)/N
x <- x + media(y-x)
```

`K_i` é o número real de minibatches do cliente, incluindo o último incompleto; `N=5`. Os controles iniciam em zero. O controle global e todos os controles locais são salvos em `rodada-00.pt`, `rodada-01.pt` e `rodada-02.pt`. O teste escalar recarrega a rodada 1 em outro processo e verifica igualdade bit a bit com a execução contínua até a rodada 2. As recargas usam `weights_only=True`. A persistência da simulação CNN é conferida por round-trip dos estados e pela cadeia de hashes de `ci` entre rodadas.

## Dados e métricas

Reutiliza [manifesto_validacao.npz](../cnn-validacao/particao/manifesto_validacao.npz), SHA-256 `bb710d6492ac83456b61ba8469d06f6729bf063ba586a557b0165a701173339f`. O carregador existente reconfere os índices, grupos e vetores em float32. São 203.251 exemplos de ajuste e 50.815 de validação. A média e o desvio ddof=0 são calculados só no ajuste; escala constante vira 1. Timestamp e identificadores não são features. As 81 features em ordem literal, o mapa 0=BENIGN/1=DDoS e a normalização ficam no contrato e no checkpoint.

`score` é a sigmoide do logit DDoS, sem calibração de probabilidade. O limiar operacional é escolhido separadamente por método na validação: maior recall respeitando FPR≤1%; empates por menor FP e maior limiar. Predição `score >= limiar`. O limite permite no máximo 407 FP entre 40.776 BENIGN. Nenhuma seleção de taxa, número de rodadas ou outro hiperparâmetro é feita pelas métricas. Este recall é exploratório, pois a mesma validação escolhe o limiar e mede desempenho. O teste global não é inferido nem usado para seleção.

## Saídas

A execução registrada está em [ensaio-01/](ensaio-01/). Em cada pasta de reprodução:

- `teste_controles/resultado.json`: oráculo manual e retomada do teste escalar; logs ao lado.
- `execucao/configuracao.json`, `clientes.npz`, `pesos_iniciais.pt`: configuração prévia e pareamento.
- `execucao/{fedavg_sgd,scaffold}/checkpoint.pt`: CNN, normalização e contrato.
- `execucao/{fedavg_sgd,scaffold}/rodada-XX.pt`, `rodadas.json`, `treino.json`: estados de controles, participantes, exemplos, passos, bytes e tempo.
- `execucao/{fedavg_sgd,scaffold}/scores_validacao.npy`, `execucao/resultados.json`: scores, limiares, recall, FPR, macro-F1 e matrizes.
- `execucao/pareamento.json`, `recarga.log`: igualdade da rodada inicial e reprodução dos scores em outro processo.

Os bytes são o volume bruto dos arrays float32 de parâmetros (Δpesos na subida) e controles (`c` na descida, `Δci` na subida) na simulação em processo. Não incluem envelopes Flower, serialização, rede ou persistência em disco. Não são bytes medidos em rede.

Código e configurações estão na pasta ignorada `secfednet-local/`. Para reprodução por outra pessoa, será necessário incluir estes scripts, o protocolo, os manifestos e suas dependências locais no inventário do primeiro commit, com autorização de Willian. Veja também [PRIMEIRO_COMMIT.md](../cnn-validacao/PRIMEIRO_COMMIT.md). O benchmark longo, outras seeds e captura independente seguem pendentes.
