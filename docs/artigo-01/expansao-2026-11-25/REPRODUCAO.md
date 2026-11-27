# Reprodução e dependências externas

Execute os comandos desta página a partir da pasta que contém este arquivo. Caminhos da entrega são relativos. O dataset é externo; destinos devem ser novos. Não executar treino na árvore de evidências. A verificação documental não instala pacotes, não treina nem avalia sexta.

```bash
python3 -B verificar.py
python3 -B verificar_auditoria.py fonte/auditoria_referencia
```

O lock foi executado em Linux x86_64/Ubuntu26.04.1, glibc2.43, CPython3.14.4; NumPy2.3.5, Torch2.12.1+cpu, Flower1.32.0. A wheel Torch fixada é cp314/manylinuxx86_64; não se afirma validação em outras plataformas. [Lock de 41 pacotes](fonte/requirements.lock). `uv` de bootstrap na VM era0.13.10; o pacote uv interno do lock é0.11.33.

Obtenha `CICIDS2017_improved.zip` na distribuição dos autores, sem renomear versões diferentes. A documentação do insumo e os hashes por membro estão no [inventário](fonte/inventario_cinco_capturas.json). O hash esperado é conferido antes do processamento.

```bash
curl --fail --location 'https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip' --output /dados/CICIDS2017_improved.zip
sha256sum /dados/CICIDS2017_improved.zip
uv --no-config venv --python /usr/bin/python3.14 --no-python-downloads /tmp/secfednet-ambiente-novo
uv --no-config pip sync --strict --python /tmp/secfednet-ambiente-novo/bin/python --default-index https://pypi.org/simple fonte/requirements.lock
uv --no-config pip check --python /tmp/secfednet-ambiente-novo/bin/python
```

SHA-256 ZIP: `97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`. Não há download automático nos scripts de preparação. Instalação offline requer o cache previamente preenchido; caso contrário o comando acima usa os índices registrados.

Auditoria independente, incluindo o caso sintético:

```bash
/tmp/secfednet-ambiente-novo/bin/python -B fonte/fontes/auditar_split.py sintetico /tmp/secfednet-sintetico-novo
/tmp/secfednet-ambiente-novo/bin/python -B fonte/fontes/auditar_split.py auditar /dados/CICIDS2017_improved.zip fonte/inventario_cinco_capturas.json fonte/contrato_features_referencia.json /tmp/secfednet-auditoria-nova
python3 -B verificar_auditoria.py /tmp/secfednet-auditoria-nova
```

Reprodução do candidato + logística + CNN de integração, com recargas em processos separados:

```bash
bash fonte/reproduzir.sh /tmp/secfednet-candidato-novo /tmp/secfednet-ambiente-novo/bin/python /dados/CICIDS2017_improved.zip
```

Gera `candidato/` (matrizesbrutas float64, entradasfloat32, alvos, máscaras/índices, normalizador, contrato/qualidade/interseções), `baseline/` e `fedavg_integracao/` (checkpoints, scores de quinta, configuração, métricas, recargas), logs e testes. Reservar ~3GiB de RAM livre, vários GiB de disco e espaço para swap conforme a VM original. Não gera métricas de desempenho da sexta: só prepara/confere sua qualidade e interseções.

O gate histórico compara a reprodução com [referencia_kubuntu.json](controle/referencia_kubuntu.json). SHA de checkpoint pode diferir porque contém hash de manifesto que inclui tempo/RSS; pesos, dados, scores e métricas devem coincidir, como nos231 checks. [Prova da diferença apenas de metadado](vm/logs/prova_checkpoints_apos_execucao.log).

Comparação CNN completa em nova pasta da VM: use uma cópia limpa do repositório para registrar seu estado. O preparador abaixo só copia fontes/controle e escreve uma configuração de caminhos no destino novo; não instala nem treina. Mantém o protocolo numérico histórico. `repo_estado` é apenas o alvo da consulta Git.

```bash
python3 -B preparar_rodada.py /tmp/secfednet-rodada-nova --zip /dados/CICIDS2017_improved.zip --repo /caminho/clone/secfednet --uv /home/williian/.local/bin/uv --python /usr/bin/python3.14 --cache /tmp/secfednet-uv-cache
cd /tmp/secfednet-rodada-nova
nohup setsid timeout --signal=TERM --kill-after=20s 2700s /usr/bin/python3.14 -u -B controle/executar_job.py > execucao.log 2>&1 < /dev/null &
tail -F execucao.log
```

Supervisor reconstrói lock, roda `reproduzir.sh`, exige gate, executa os seis treinos em sequência, escreve `STATUS.json`, configurações anteriores aos treinos, resultados/históricos/recargas e `tabelas/`. Artefatos completos ficam no destino; `retorno/` contém só relatório/tabelas/logs/manifesto. Reserve interno44min/externo45 min. Reiniciar sempre em novo destino. Os caminhos históricos efetivamente usados continuam em [manifesto VM](vm/manifesto_execucao.json); ele inventaria também binários mantidos somente na VM.

Reprodução já concluída é a fonte dos resultados desta entrega. Este fechamento só reexecuta verificações documentais, sintéticas, de módulos e da preparação existente, sem novo experimento. Dados e artefatos externos estão identificados em [ACERVO.json](ACERVO.json). Nenhum dataset, ZIP, checkpoint, score, ambiente ou cache é distribuído neste commit.
