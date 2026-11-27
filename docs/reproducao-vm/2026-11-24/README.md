# Evidências da reprodução na VM · Artigo 01

Revisão da reprodução de 24/11/2026, baseada em **0b38f255af6f22e4642c584c0f0e09b15ef9263e**. Esta pasta acrescenta evidências à entrega original de 90 arquivos; não muda modelos, protocolos, dados ou manifestos históricos.

- [Relatório de duas rodadas](RELATORIO_REPRODUCAO_VM.md).
- [Relatório de vinte rodadas](RELATORIO_REPRODUCAO_VM_20_RODADAS.md).
- [Inferência verificada na VM](pacote-inferencia/cnn1d/saida_verificada.json).
- [Acervo completo, procedência e hashes consultados na VM](ACERVO.json).
- [Lista exata desta seleção](LISTA_ARQUIVOS.txt) e [manifesto desta seleção](SHA256_REPRODUCAO).

## Conferir em uma cópia limpa

Na raiz do repositório, Python 3.11 ou superior e somente biblioteca padrão:

```bash
doc=docs/reproducao-vm/2026-11-24
python3 -B "$doc/verificar.py"
(cd "$doc" && sha256sum -c SHA256_REPRODUCAO --quiet)
```

O verificador exige seleção fechada, valida os 89 hashes de `SHA256_ENTREGA`, os originais selecionados contra o inventário da VM, as 40 linhas das curvas e os CSVs por método contra a baseline. Recalcula FPR, recall e macro-F1 das matrizes (tolerância absoluta 1e-12), suporte, teto de FPR, bytes acumulados e saída de inferência. Não precisa do dataset, de checkpoint, de Git nem de NumPy/PyTorch. O manifesto exclui somente seu próprio arquivo; a lista inclui todos os arquivos desta pasta. Grave novos resultados fora dela para preservar a seleção fechada.

Essa conferência documental não executa o modelo. A igualdade dos binários ausentes usa o inventário consultado diretamente na VM; pode ser recalculada no acervo:

```bash
acervo=/home/willian/Projetos/secfednet/secfednet-local/artigo-01/reproducao-vm/2026-11-25_15-41-13/backup-vm/secfednet-repro
python3 -B "$doc/verificar.py" --acervo "$acervo"
```

O destino é um acervo local, não uma dependência de caminho fixo: substitua `acervo` pela raiz restaurada contendo `codigo/`, `pacote-inferencia/` e os dois relatórios. Os caminhos dos 256 arquivos em `ACERVO.json` são relativos a essa raiz. O backup preserva também os dois registros de execução adicionais e INDEX/STATUS gerados na VM. `.git` e duas virtualenvs ficaram fora; caches e ambientes são reconstruíveis pelos locks. Não há lacunas entre os arquivos regulares inventariados e o backup.

## Executar as verificações originais

São preservados os três scripts auxiliares originais, sem alterações. A partir da raiz de uma cópia limpa, com o Python do lock de treino já preparado segundo os relatórios:

```bash
base=secfednet-local/artigo-01
py="$base/cnn-flower/.venv/bin/python"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="integracao/artigo-01:$base/cicids2017-corrigido:$base/cnn-flower:$base/cnn-flower-entrega:$base/cnn-flower-clientes:$base/cnn-fedprox:$base/cnn-validacao"
curto=codigo/secfednet-local/artigo-01/execucoes/scaffold-curto-vm-20261124-221130
longo=codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013
"$py" -B "$doc/$curto/comparar.py" "$acervo/$curto" > /tmp/secfednet-comparacao-curta.json
"$py" -B "$doc/$curto/verificar_checkpoints.py" "$acervo/$curto"
"$py" -B "$doc/$longo/comparar_referencia.py" "$acervo/$longo" > /tmp/secfednet-comparacao-20.json
```

O primeiro script usa os scores e índices curtos que já pertencem à baseline. Os checkpoints e scores da VM são lidos do acervo. A recarga usa `torch.load(..., weights_only=True, map_location="cpu")`. Alterações de configuração são feitas só em cópias temporárias. Os comandos dos relatórios são históricos: seus destinos `secfednet-local/artigo-01/execucoes/...` identificam a árvore original da VM, preservada sob `codigo/` no acervo. Não use esses destinos já existentes como saída de um novo treino.

## Inferência e reprodução completa

O [contrato da CNN](../../../integracao/artigo-01/contrato-cnn/CONTRATO.md) e o [registro do pacote](../../../integracao/artigo-01/contrato-cnn/pacote_inferencia.json) fazem parte da baseline. O ZIP separado, fora do Git, tem SHA-256 **e7d042b38c77b96bef54533302bef817d6b8a4a8e55b717bac7b32f98b5b6014**. No acervo ele está em `pacote-inferencia/secfednet-cnn1d-v1.zip`; a pasta extraída inclui `saida_verificada.json`.

Em uma pasta temporária nova, extraia o ZIP, confira `SHA256SUMS` e siga seu README/requirements.lock. Com o Python de inferência preparado:

```bash
# Na pasta extraída, sem dataset e sem PYTHONPATH do repositório:
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -I -B cnn1d.py \
  checkpoint_cnn1d.pt exemplo_entrada.json > saida_verificada.json
cmp exemplo_saida.json saida_verificada.json
```

A saída registrada é classe `DDoS` (id 1), score `0.987495481967926` e embedding com 16 valores. São 81 features brutas, na ordem do contrato, média/desvio do treino embutidos, score sigmoide não calibrado para DDoS e limiar inclusivo 0,5. Essa inferência pertence ao pacote da CNN e não aos checkpoints exploratórios SCAFFOLD.

Para refazer o treino, siga os relatórios e os [wrappers originais](../../../secfednet-local/artigo-01/cnn-scaffold/README_20.md), sempre com saída nova. Dados: distribuição corrigida dos autores, `https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip`, SHA-256 **97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883** (343.549.013 bytes). Reaproveite o ZIP verificado em `codigo/secfednet-local/artigo-01/cicids2017-corrigido/` no acervo ou baixe dessa URL e confira o hash. Ambientes são recriados pelo lock de treino versionado em `secfednet-local/artigo-01/cnn-flower/requirements.lock`. A VM usou CPython 3.14.4, PyTorch 2.12.1+cpu, Flower 1.32.0, NumPy 2.3.5, Ubuntu 26.04.1 x86-64/glibc 2.43. O kernel da referência era -43 e o da VM -44.

O treino gera índices dos clientes, configuração, estados/pesos/controles, scores, curvas, métricas, checkpoints, logs e tempos. Os binários, dataset, bundle e ambientes continuam fora deste commit; o inventário registra seus hashes. O bundle preservado no acervo é `secfednet-artigo01.bundle`, SHA-256 **67b121886f947ee5b9eb13f4b10501b713bd777f1cdc619b075bd625af1676d7**.

## Resultado e limites

| Ponto | Recall DDoS | FP | FPR | Macro-F1 | Bytes brutos acumulados |
| --- | ---: | ---: | ---: | ---: | ---: |
| FedAvg-SGD 20 | 99,1633% | 406 | 0,995684% | 0,984974069 | 919.200 |
| SCAFFOLD 20 | 74,7186% | 407 | 0,998136% | 0,900356695 | 1.838.400 |
| SCAFFOLD 10 | 0,2690% | 406 | 0,995684% | 0,445435760 | 919.200 |

A validação interna tem 40.776 BENIGN e 10.039 DDoS. Limiar e métrica usam essa mesma validação; resultados exploratórios, sem avaliação nova do teste congelado. Os bytes são arrays brutos de parâmetros/controles na simulação em processo, não tráfego de rede serializado. Os relatórios detalham a igualdade dos 42 estados e 40 scores de vinte rodadas e as diferenças de plataforma e tempo. Os três históricos sem saída do wrapper (`auditoria_curvas.json`, `fontes.log`, `preservacao.log`) permanecem explicitados, não tratados como cópia perdida.
