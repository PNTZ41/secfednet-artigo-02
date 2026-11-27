# Evidência parcial de Gabriel

O material identificado contém duas frentes distintas. A [ficha CICIDS2017 original](../../../SecFedNet_CICIDS2017_entrega/ficha_CICIDS2017.md) e o CSV local SHA `6ff1580f5f81c0ae28a26f7631721018577f5f7c5e0feac28b795fcfe7b411ee` descrevem 225.745 registros, 78 atributos, BENIGN97.718 / DDoS128.027. É a caracterização histórica do recorte de sexta original, não as cinco capturas corrigidas com 81 features.

Também foi localizado `SecFedNet_UNSW-NB15_auditoria.zip`, SHA `9334cbae93e244f94c2bb46d6fd9621aae0e4809f6bd4a190dcff1eab62a5933`. O manifesto interno foi conferido contra todos os membros. Incluímos o [script de contagem](gabriel/unsw-nb15/count_classes.py), [procedência declarada](gabriel/unsw-nb15/docs/dataset_source.md), [esquema/hashes declarados](gabriel/unsw-nb15/results/dataset_audit.json) e [contagens binárias](gabriel/unsw-nb15/results/class_counts_binary.csv) / [nominais](gabriel/unsw-nb15/results/class_counts_multiclass.csv). As contagens declaradas são treino175.341 (Normal56.000/ataque119.341), teste82.332 (Normal37.000/ataque45.332). Não são nova medição dos dados brutos nesta rodada.

Faltam os insumos identificados na auditoria anterior: `Arquivo compactado.zip`, SHA `04a48a9e386a8a3836d9d807d2ad1502c3a6e68c34788a71d534c3b644470b82`, ou ambos `UNSW_NB15_training-set.csv` (SHA `bec7dd5ec88dc2a0ccc7a07879d338395ed7421750f675fd0339e07dfe0648fa`) e `UNSW_NB15_testing-set.csv` (SHA `734fe6642edf758f7c94d7d9149426b49d202fe8e7bf0bef47392489c3c0a559`). O pacote de auditoria não contém esses CSVs. A evidência é parcial: integridade dos documentos e resultados fornecidos, sem reprodução independente da contagem nem da ausência de sobreposição nas42 features. Não se usa UNSW no desempenho reportado do CICIDS2017.

Quando houver o insumo, em destino novo:

```bash
python3 -B gabriel/unsw-nb15/count_classes.py --source '/caminho/Arquivo compactado.zip' --out-dir /tmp/unsw-recheck-novo
```
