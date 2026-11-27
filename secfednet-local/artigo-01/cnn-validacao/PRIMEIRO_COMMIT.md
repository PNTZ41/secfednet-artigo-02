# Arquivos para reproduzir a validação do Artigo 01

Este é o inventário do primeiro commit a autorizar. Os caminhos abaixo são os atuais e formam a cadeia de imports do ensaio. `secfednet-local/` está ignorado pelo Git. Os arquivos selecionados dessa pasta precisarão de inclusão explícita ou de uma reorganização equivalente dos imports antes do commit.

## Código e ambiente

```text
AGENTS.md
.gitignore
integracao/artigo-01/piloto_fedavg.py
integracao/artigo-01/avaliar_piloto.py
secfednet-local/artigo-01/cicids2017-corrigido/avaliar_corrigido.py
secfednet-local/artigo-01/cnn-flower/cnn1d.py
secfednet-local/artigo-01/cnn-flower/treinar_cnn.py
secfednet-local/artigo-01/cnn-flower/requirements.lock
secfednet-local/artigo-01/cnn-flower-entrega/prever_suporte_clientes.py
secfednet-local/artigo-01/cnn-flower-entrega/treinar_instrumentado.py
secfednet-local/artigo-01/cnn-flower-clientes/avaliar_clientes.py
secfednet-local/artigo-01/cnn-fedprox/experimentar_fedprox.py
secfednet-local/artigo-01/cnn-validacao/validar_mu.py
secfednet-local/artigo-01/cnn-validacao/reproduzir.sh
secfednet-local/artigo-01/cnn-validacao/protocolo.json
secfednet-local/artigo-01/cnn-validacao/PRIMEIRO_COMMIT.md
secfednet-local/artigo-01/cnn-validacao/SHA256_FONTES
```

## Manifestos, configuração e referência de resultado

```text
secfednet-local/artigo-01/cicids2017-corrigido/split_cronologico.npz
secfednet-local/artigo-01/cnn-validacao/particao/protocolo.json
secfednet-local/artigo-01/cnn-validacao/particao/manifesto_validacao.npz
secfednet-local/artigo-01/cnn-validacao/particao/auditoria.json
secfednet-local/artigo-01/cnn-validacao/execucao/configuracao.json
secfednet-local/artigo-01/cnn-validacao/execucao/selecao.json
secfednet-local/artigo-01/cnn-validacao/execucao/teste_calibracao.json
```

Inclua também `validacao.json` e `treino.json` de cada um dos quatro métodos em `cnn-validacao/execucao/`. Eles registram o resultado de referência, bytes e tempos. O relatório desta missão, listado em `INDEX.md`, documenta hashes, suporte, regras e limitações. O ambiente virtual e o ZIP de dados serão recriados no computador de quem reproduzir.

## Obtenção dos dados e execução

O download tem 343.549.013 bytes. O membro usado é `friday.csv` da versão corrigida CNS 2022 dos autores. SHA-256 esperado do ZIP `97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`.

```bash
mkdir -p secfednet-local/artigo-01/cicids2017-corrigido
curl --fail --location \
    https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip \
    --output secfednet-local/artigo-01/cicids2017-corrigido/CICIDS2017_improved.zip
sha256sum secfednet-local/artigo-01/cicids2017-corrigido/CICIDS2017_improved.zip
uv venv --python 3.14.4 secfednet-local/artigo-01/cnn-flower/.venv
uv pip sync --python secfednet-local/artigo-01/cnn-flower/.venv/bin/python \
    --default-index https://pypi.org/simple secfednet-local/artigo-01/cnn-flower/requirements.lock
bash secfednet-local/artigo-01/cnn-validacao/reproduzir.sh /tmp/secfednet-validacao-nova
```

O lock usa PyTorch CPU 2.12.1 para CPython 3.14, Linux x86-64. O ensaio local usa Python 3.14.4, Flower 1.32.0 e NumPy 2.3.5. A pasta de saída do comando final deve estar inexistente. O script registra a configuração antes de treinar e gera somente métricas da validação. O limiar selecionado está em `selecao.json`; o `limiar=0.5` do contrato de treinamento permanece como referência não calibrada.

O revisor e a skill locais, se forem incluídos como convenções do projeto, estão em `.codex/agents/secfednet_revisor_defensivo.toml` e `.agents/skills/secfednet-validar-experimento/SKILL.md`.

## SCAFFOLD: piloto e extensão de 20 rodadas

Acrescentar os seguintes arquivos ao conjunto a revisar para o primeiro commit. A autorização de commit continua pendente; nada foi adicionado ao index do Git. Os caminhos estão sob a pasta ignorada e precisam ser mantidos ou reorganizados junto aos imports e caminhos de referência.

```text
secfednet-local/artigo-01/cnn-scaffold/scaffold.py
secfednet-local/artigo-01/cnn-scaffold/testar_controles.py
secfednet-local/artigo-01/cnn-scaffold/experimentar_scaffold.py
secfednet-local/artigo-01/cnn-scaffold/protocolo.json
secfednet-local/artigo-01/cnn-scaffold/reproduzir.sh
secfednet-local/artigo-01/cnn-scaffold/README.md
secfednet-local/artigo-01/cnn-scaffold/experimentar_20.py
secfednet-local/artigo-01/cnn-scaffold/protocolo_20.json
secfednet-local/artigo-01/cnn-scaffold/reproduzir_20.sh
secfednet-local/artigo-01/cnn-scaffold/README_20.md
secfednet-local/artigo-01/cnn-scaffold/SHA256_FONTES
secfednet-local/artigo-01/cnn-scaffold/SHA256_FONTES_20
secfednet-local/artigo-01/cnn-scaffold/SHA256_ARTEFATOS
secfednet-local/artigo-01/cnn-scaffold/SHA256_ARTEFATOS_20
secfednet-local/artigo-01/cnn-scaffold/SHA256_PRESERVADOS
secfednet-local/artigo-01/cnn-scaffold/SHA256_PRESERVADOS_20
```

A extensão usa explicitamente estas referências do piloto das 12h37 para conferir inicialização, partições e reprodução das duas primeiras rodadas. Incluí-las permite executar o script sem depender de arquivos locais não documentados:

```text
secfednet-local/artigo-01/cnn-scaffold/ensaio-01/execucao/configuracao.json
secfednet-local/artigo-01/cnn-scaffold/ensaio-01/execucao/clientes.npz
secfednet-local/artigo-01/cnn-scaffold/ensaio-01/execucao/fedavg_sgd/treino.json
secfednet-local/artigo-01/cnn-scaffold/ensaio-01/execucao/fedavg_sgd/scores_validacao.npy
secfednet-local/artigo-01/cnn-scaffold/ensaio-01/execucao/scaffold/treino.json
secfednet-local/artigo-01/cnn-scaffold/ensaio-01/execucao/scaffold/scores_validacao.npy
```

Guardar também as referências de resultados da extensão em `cnn-scaffold/ensaio-20-rodadas/execucao/`: `configuracao.json`, `clientes.npz`, `comparacoes.json`, `resultados.json`, `curvas.csv`, `pareamento.json`, `verificacao_independente.json` e `tempo.json`; de cada método, `curva.json`, `curva.csv`, `rodadas.json` e `treino.json`. Os checkpoints, estados e scores permitem auditoria e são regeneráveis pelo comando abaixo. O manifesto `SHA256_ARTEFATOS_20` lista seus hashes para a execução de referência, incluindo logs. Se os binários forem guardados fora do commit, manter sua localização e o mecanismo de obtenção documentados; os hashes de arquivos PyTorch/NPZ podem variar entre ambientes mesmo com arrays iguais.

Comando adicional, da raiz, com destino inexistente:

```bash
bash secfednet-local/artigo-01/cnn-scaffold/reproduzir_20.sh /tmp/secfednet-scaffold-20-novo
```

O ambiente e os dados são os mesmos já descritos acima. Os dois métodos usam SGD lr=0,01 e agregação uniforme; o teste global permanece congelado. A comparação usa os pontos previamente fixados 20/20 rodadas e FedAvg 20/SCAFFOLD 10 para igualdade de bytes brutos, sem selecionar a melhor rodada pela curva.
