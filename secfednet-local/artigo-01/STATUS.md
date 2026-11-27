# Artigo 01 · Estado em 27/11/2026

Os registros, os scripts de auditoria e as evidências da rodada 10 estão no commit local «Versiona registros e scripts da auditoria do SecFedNet». A verificação de `SHA256_ENTREGA` passou. [Registro do commit](execucoes/2026-11-27/RELATORIO_2026-11-27_10-27-09_BRT_commit_acervo_secfednet.md)

O commit local `190603c` em `integracao/artigo-01` registra os mesmos três Markdown em `docs/artigo-02/relatorios/`. A árvore coincide com a publicada no repositório do Artigo 02. O commit está um passo à frente da referência local de `origin/integracao/artigo-01`. [Registro do commit local](execucoes/2026-11-27/RELATORIO_2026-11-27_10-19-31_BRT_commit_relatorios_secfednet.md)

Os dois relatórios de síntese e o índice foram publicados em `PNTZ41/secfednet-artigo-02`, branch `main`, commit `d5a9364`. A árvore remota coincide com a do commit local `21748a3`. [Conferência da publicação](execucoes/2026-11-27/RELATORIO_2026-11-27_10-07-59_BRT_publicacao_verificada.md)

Auditoria documental do baseline FedAvg concluída. Na validação de quinta, os FN limpos são 65.102, 70.613 e 71.449 nas seeds 23, 41 e 89. A sexta permanece reservada.

Próximo passo: decidir a política de colisões float32, conflitos e cobertura de validação, depois conferir os identificadores e denominadores pareados por seed e tipo antes dos ensaios de backdoor.

[Relatório da auditoria](execucoes/2026-11-26/RELATORIO_2026-11-26_11-04-56_BRT_auditoria_metodologica_fedavg.md)

[Proposta de protocolo BENIGN × DDoS](execucoes/2026-11-26/RELATORIO_2026-11-26_11-21-13_BRT_proposta_protocolo_ddos.md) redigida para revisão. Próximo passo desta frente: identificar capturas independentes com suporte DDoS e esquema compatível, verificar elegibilidade por cliente e fechar marcador e precisão amostral. A sexta da expansão segue reservada.

[Auditoria das capturas, do suporte e das métricas BSR](execucoes/2026-11-26/RELATORIO_2026-11-26_11-34-25_BRT_capturas_dose_bsr.md) concluída. O acervo documenta suporte histórico para 23/2305 e permite projetar as contagens das outras seeds no mesmo pool. Faltam as capturas independentes de desenvolvimento. O próximo passo é documentar sua procedência, conferir o esquema e a disjunção por campanha e recontar o suporte efetivo. Denominadores e contrastes pareados da BSR estão definidos no relatório. A sexta permanece reservada.

[Retomada limpa da rodada 10 e auditoria FedAvg-SGD](execucoes/2026-11-26/RELATORIO_2026-11-26_23-09-05_BRT_retomada_fedavg_10_auditoria.md). A agregação auditada reproduziu o controle em tensores sintéticos. Para executar a rodada real, obter os quatro artefatos da VM, a exportação de ajuste e validação interna e o ambiente de referência. A sexta reservada não entra na retomada.

[Conferência de recebimento no Kali em 26/11](execucoes/2026-11-26/RELATORIO_2026-11-26_23-17-52_BRT_recebimento_retomada_10.md). Naquela conferência, a pasta de destino ainda estava vazia.

[Ambiente e fonte da retomada](execucoes/2026-11-27/RELATORIO_2026-11-27_08-34-25_BRT_ambiente_retomada_10_e_fonte.md). Os quatro artefatos da VM foram recebidos e conferidos, e o ambiente de referência foi preparado antes da chegada do ZIP.

[Rodada 10 limpa reproduzida bit a bit](execucoes/2026-11-27/RELATORIO_2026-11-27_08-49-40_BRT_retomada_10_reproduzida.md). O ZIP foi verificado, a exportação interna foi gerada e a rodada 10 foi executada. Pesos e scores coincidem com a VM, inclusive nos arquivos serializados. A retomada está concluída. Preservar a saída auditada como referência. O teste reservado segue fora desta reprodução.
