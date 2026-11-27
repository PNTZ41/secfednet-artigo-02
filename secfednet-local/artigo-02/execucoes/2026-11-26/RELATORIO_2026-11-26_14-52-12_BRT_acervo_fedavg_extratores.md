# Artigo 02 · Auditoria do checkpoint FedAvg e dos extratores

26/11/2026, 14:52:12, Belém (UTC−03). Objetivo: recuperar o estado da rodada 20 e o normalizador original, conferir os hashes e localizar material pareado para comparar as extrações CICIDS2017 e CSE-CIC-IDS2018 corrigidas. [Relatório de compatibilidade](RELATORIO_2026-11-26_11-56-51_BRT_compatibilidade_cicids2018.md).

## Checkpoint e cópias da VM

**O SHA-256 esperado coincide com os registros da referência e da VM. O binário está ausente dos caminhos acessíveis, portanto não foi possível recalcular seu hash nesta missão.** A seleção documental no checkout inclui 22 arquivos da execução de 20 rodadas da VM. Recalculei os 22 hashes e todos conferem com o inventário. Isso verifica a cópia dos documentos, incluindo a configuração e a comparação histórica. [Inventário do backup](../../../../docs/reproducao-vm/2026-11-24/ACERVO.json) · [Comparação histórica](../../../../docs/reproducao-vm/2026-11-24/codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/comparacao_referencia.json) · [Manifesto da referência](../../../artigo-01/cnn-scaffold/SHA256_ARTEFATOS_20).

| Local | Caminho | Evidência desta missão |
|---|---|---|
| Referência local | `secfednet-local/artigo-01/cnn-scaffold/ensaio-20-rodadas/execucao/fedavg_sgd/rodada-20.pt` | Arquivo ausente. Manifesto e registro do treino trazem o SHA-256 `142064a63d95363767470dd17802643dea9abad1ef5dd7e905caa6b521fb2b86`. |
| Execução da VM | `/home/williian/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/execucao/fedavg_sgd/rodada-20.pt` | Raiz ausente neste ambiente. Inventário registra 46.903 B e o mesmo SHA-256. |
| Backup completo | `/home/willian/Projetos/secfednet/secfednet-local/artigo-01/reproducao-vm/2026-11-25_15-41-13/backup-vm/secfednet-repro/codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/execucao/fedavg_sgd/rodada-20.pt` | Raiz ausente neste ambiente. Caminho derivado de `backup_completo` e da entrada do arquivo em `ACERVO.json`. |
| Cópia documental | `docs/reproducao-vm/2026-11-24/codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/` | Diretório presente. Os 22 arquivos locais listados no inventário têm SHA-256 correspondente. `execucao/fedavg_sgd/rodada-20.pt` e `checkpoint.pt` não fazem parte dessa seleção. |

A busca incluiu checkout e histórico Git, diretórios locais e montagens disponíveis, por nome de artefato e extensões de disco, pacote e captura. A inspeção do diretório dos dois ZIPs de contexto do IDE encontrou apenas marcadores. Não houve acesso remoto à VM. [Escopo da seleção da VM](../../../../docs/reproducao-vm/2026-11-24/README.md).

## Parâmetros originais de normalização

A rotina de `rodada-20.pt` serializa número da rodada, pesos e controles. **Os vetores originais estão em `execucao/fedavg_sgd/checkpoint.pt` da mesma execução**, nas chaves `media` e `escala`, junto ao `state_dict`, contrato, método e hash da configuração. O arquivo final está ausente tanto da seleção documental da VM quanto do diretório da referência. O inventário registra 12.789 B para o arquivo final da VM. O SHA-256 do arquivo final difere entre referência e VM. A verificação histórica atribuiu a diferença ao campo `configuracao_sha256`, pois a configuração registra kernels distintos. Os dois arquivos finais têm identidades esperadas distintas. [Serialização do estado](../../../artigo-01/cnn-scaffold/scaffold.py#L90) · [Serialização do modelo final](../../../artigo-01/cnn-scaffold/experimentar_scaffold.py#L142) · [Relatório histórico da VM](../../../../docs/reproducao-vm/2026-11-24/RELATORIO_REPRODUCAO_VM_20_RODADAS.md).

| Objeto | SHA-256 registrado |
|---|---|
| `checkpoint.pt` da VM | `4e73b24cf7042eace103969787d86f07084ddc4eb558a01fe3bcf32562898922` |
| `checkpoint.pt` da referência local | `909d34c1c4d70e3485ac436b509aeb58bc14ea3d779cac97ec9c5dd3b8c6412d` |
| Bytes do vetor `media`, referência e VM | `e7e9d309135e77b7f5b52927fc308f7c309a4d7a6afc95d7fefd05ac41528ad4` |
| Bytes do vetor `escala`, referência e VM | `ba674fa6edf9f9e89a4d085937db2397d1e702298c4dfa1900090f8b30b44d70` |

Conferi a igualdade dos digests registrados para os vetores e para o manifesto de validação entre as duas configurações. Também recalculei os SHA-256 de `clientes.npz` e `manifesto_validacao.npz` locais, que correspondem aos registros (`bbb35ecd842ddf7924e6b9d884d096a36bac01a258affaee27af34b592ddaffb` e `bb710d6492ac83456b61ba8469d06f6729bf063ba586a557b0165a701173339f`). São arquivos de índices, sem os parâmetros do normalizador. [Configuração local](../../../artigo-01/cnn-scaffold/ensaio-20-rodadas/execucao/configuracao.json) · [Configuração da VM](../../../../docs/reproducao-vm/2026-11-24/codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/execucao/configuracao.json).

A escala efetiva é desvio populacional do ajuste (ddof=0), com zero substituído por 1. A operação usa float64 antes da conversão da entrada para float32. A planilha `preprocessamento_por_feature.csv` tem 81 valores por vetor, mas seus digests em float64 little-endian são `6113f268ee3e61190f81232407291362e6bb52ce8d4d3afb09216e4f153f12c7` e `14ea622356df71e0d5c7bbb5ba2d6f78e78eefcb2e7f6995ac040aa098968731`. Ela pertence à expansão semanal BENIGN × ATTACK. [Rotina de ajuste](../../../artigo-01/cnn-validacao/validar_mu.py#L124) · [Tabela de outro normalizador](../../../../docs/artigo-01/expansao-2026-11-25/candidato/preprocessamento_por_feature.csv).

## Extratores e comparação numérica

O acervo fornece o contrato de entrada, o cabeçalho dos dois dias de 2018 e referências ao fork público e ao notebook dos autores. A configuração da VM identifica o ambiente de treino, sem vincular um executável CICFlowMeter aos CSVs efetivamente usados. Na busca não encontrei dois registros de extração com commit ou hash de binário e parâmetros efetivos. Também não encontrei um PCAP de referência comum ou dois CSVs de saída provenientes dos mesmos pacotes. Os prefixos de 2018 preservados no Artigo 02 fornecem cabeçalhos e contagens, sem pares de vetores. [Evidência de cabeçalhos](EVIDENCIA_2026-11-26_cicids2018_cabecalhos.json) · [Regras documentadas no relatório anterior](RELATORIO_2026-11-26_11-56-51_BRT_compatibilidade_cicids2018.md).

| Prioridade | Conhecimento documental disponível | Insumo que falta para a comparação |
|---|---|---|
| Duração zero | O serializador público consultado no relatório anterior usa −1 nas taxas globais com duração zero e zero nas taxas direcionais quando a duração não é positiva. | Vetores das duas versões para o mesmo fluxo de duração zero e registro de linhas descartadas na exportação. A regra pública não comprova as duas saídas. |
| Conversões inteiras | O notebook de referência usa int16 para comprimentos de cabeçalhos, int32 para subfluxos e int64 para `Total TCP Flow Time`. | Saídas pareadas antes e depois das conversões, incluindo um valor de cabeçalho acima do limite int16 e um quociente de subfluxo fracionário. Identificar a biblioteca e a versão responsáveis por converter. |
| Duração acumulada | O código público acumula duração e pode herdar estado e lacunas entre segmentos. O relatório anterior registra que a lógica consultada também trata UDP. | Mesmos pacotes e vetores para uma conexão TCP que atravesse o timeout e depois termine, com a ordenação e os timeouts efetivos. Uma linha CSV isolada não permite reconstruir o acumulador. |

A comparação dos vetores segue pendente nos três casos. Nenhum ZIP completo foi baixado, nenhuma inferência foi executada e nenhum dado da sexta reservada foi acessado.

## Solicitação exata ao William

1. Do mesmo diretório `codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/execucao/fedavg_sgd/` do backup inventariado, enviar **`rodada-20.pt` e `checkpoint.pt` originais**, com seus caminhos de origem e a saída de `sha256sum` para os dois. Os arquivos somam 59.692 B na cópia VM. Se só houver a execução de referência, enviar o par de lá e identificá-lo. Se faltar o arquivo final, enviar `media` e `escala` como dois vetores float64 de 81 posições em NPZ, acompanhados de `ordem_features` e do hash da configuração de origem.
2. Enviar **a identidade e configuração efetiva de cada extração** que produziu o CICIDS2017 corrigido usado no ajuste e o CSE-CIC-IDS2018 corrigido de 20/21. Para cada uma, registrar repositório e commit ou binário e SHA-256, parâmetros de timeout de fluxo e atividade com unidades, regra de sentido e término, fuso e resolução, pré-processamento de PCAP, além de notebook ou script de exportação com versão, conversões e filtros. Distinguir parâmetros efetivamente usados de padrões publicados.
3. Enviar **um PCAP/PCAPNG sintético ou de referência fora da sexta reservada**, com seu SHA-256, processado pelas duas versões. Juntar os dois CSVs brutos e os dois pós-exportação ou uma tabela pareada por fluxo, com os 81 atributos, identificação da entrada, sentido, tempo e indicação de descarte. Cobrir os três casos da tabela. Se a amostra pareada ainda não existir, o mesmo PCAP e os dois ambientes reproduzíveis permitem gerar as saídas depois.

O próximo passo é conferir o SHA-256 dos binários recebidos e os hashes dos dois vetores, depois comparar as saídas pareadas por fluxo e versão de exportação. Não é necessário transferir o backup completo.

## Registro da missão e reprodução

Branch inicial e final `integracao/artigo-01`, HEAD `4cc2727`. Alteração já presente no índice rastreado do Artigo 01 e `.idea/` já não rastreada. Registros desta missão: este relatório e `INDEX.md`/`STATUS.md` do Artigo 02. A instrução consultada foi `AGENTS.md`. `.agents/` e `.codex/` vazios. Foram usados `git status`, `git rev-parse`, `git worktree list`, `git log`, `git cat-file`, `rg`, `find`, `ls`, `sed`, `head`, `awk`, `date` e Python sem carga de modelos. Conferência documental reproduzível da raiz:

```sh
python3 -B - <<'PY'
import hashlib, json
from pathlib import Path

base = Path("docs/reproducao-vm/2026-11-24")
prefixo = "codigo/secfednet-local/artigo-01/execucoes/scaffold-20-vm-20261124-222013/"
acervo = json.loads((base / "ACERVO.json").read_text())
linhas = [x for x in acervo["arquivos"] if x["path"].startswith(prefixo)]
estado = next(x for x in linhas if x["path"].endswith("/fedavg_sgd/rodada-20.pt"))
assert estado["sha256"] == "142064a63d95363767470dd17802643dea9abad1ef5dd7e905caa6b521fb2b86"
print("Hash registrado:", estado["sha256"])
copia = Path(acervo["backup_completo"]) / estado["path"]
print("Binário inventariado acessível:", copia.is_file())
locais = [x for x in linhas if (base / x["path"]).is_file()]
assert len(locais) == 22
assert all(hashlib.sha256((base / x["path"]).read_bytes()).hexdigest() == x["sha256"] for x in locais)
print("Arquivos da seleção conferidos:", len(locais))
PY
```

Ao receber o par, rodar `sha256sum -- rodada-20.pt checkpoint.pt` no diretório de entrega e comparar com a linha correspondente à origem.
