# Artigo 02 · Estado em 26/11/2026

[Proposta de avaliação do FedAvg limpo](execucoes/2026-11-26/RELATORIO_2026-11-26_11-39-50_BRT_avaliacao_fedavg_limpo.md) registrada para revisão. O resultado histórico da rodada 20 é validação interna. A sexta-feira segue reservada para teste.

A viabilidade da avaliação independente depende de inventário por campanha e sessão, equivalência comprovada das 81 medidas e suporte BENIGN/DDoS após os filtros. O próximo passo é conferir esses metadados e fechar os manifestos de ajuste, calibração e avaliação. O limiar será escolhido exclusivamente na calibração.

[Prova de compatibilidade dos CSVs corrigidos de 20 e 21/02](execucoes/2026-11-26/RELATORIO_2026-11-26_11-56-51_BRT_compatibilidade_cicids2018.md) confirma os 81 atributos em ordem nos dois cabeçalhos. Há suporte de BENIGN e DDoS documentado pelos autores. Para qualificar a inferência com o checkpoint existente, faltam a prova de paridade numérica e um manifesto verificável por sessão e campanha com contagens após filtros. A sexta do CICIDS2017 segue reservada.

[Auditoria do checkpoint e dos extratores](execucoes/2026-11-26/RELATORIO_2026-11-26_14-52-12_BRT_acervo_fedavg_extratores.md) confirma a concordância dos hashes registrados e a integridade da seleção documental da VM. Os binários da rodada 20 e do normalizador não estão disponíveis neste checkout. O próximo passo é obter o par de arquivos FedAvg, as versões e configurações efetivas dos extratores e a amostra pareada indicados no relatório.

[Inspeção do fluxo federado e teste sintético](execucoes/2026-11-26/RELATORIO_2026-11-26_15-59-52_BRT_fluxo_fedavg_validacao_sintetica.md) concluídos. A referência FedAvg-SGD agrega deltas por média uniforme. A validação defensiva de formato foi exercitada em memória. Permanecem pendentes a escolha do baseline independente, os manifestos e a política de aceitação de contribuições no servidor. A sexta permanece reservada.
