# Origem e proveniência

Fonte institucional: https://research.unsw.edu.au/projects/unsw-nb15-dataset

Referência: Moustafa, N.; Slay, J. (2015). UNSW-NB15: a comprehensive data set for network intrusion detection systems. MilCIS. https://doi.org/10.1109/MilCIS.2015.7348942

A aquisição direta foi anteriormente reportada como bloqueada por autenticação do SharePoint. O insumo efetivamente auditado é o ZIP fornecido pelo usuário, `Arquivo compactado.zip`, SHA-256:

`04a48a9e386a8a3836d9d807d2ad1502c3a6e68c34788a71d534c3b644470b82`

Membros usados:
- `Training and Testing Sets/UNSW_NB15_training-set.csv`
- `Training and Testing Sets/UNSW_NB15_testing-set.csv`

O dicionário `NUSW-NB15_features.csv` no mesmo ZIP foi consultado. Os demais membros, inclusive o ground truth e PDF, não foram necessários para a contagem. O segundo ZIP, `UNSW-NB15_.zip`, não foi utilizado. Os hashes dos CSVs estão em `results/dataset_audit.json`. Não houve comparação com hashes autenticados pela UNSW: compatibilidade de esquema e contagens não comprova autenticidade. Os dados brutos não são redistribuídos neste pacote.
