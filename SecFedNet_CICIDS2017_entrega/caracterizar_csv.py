"""Leitura integral, sem limpeza; somente biblioteca padrao do Python."""
import argparse
import collections
import csv
import hashlib
import json
import math
import platform
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--saida', type=Path, default=Path('analise/resultado.json'))
    args = parser.parse_args()
    sha = hashlib.file_digest(args.csv.open('rb'), 'sha256').hexdigest()
    classes = collections.Counter()
    empty, nan, inf, invalid = (collections.Counter() for _ in range(4))
    seen = set()
    examples = {}
    n = duplicates = blank_records = 0
    rows_empty = rows_nan = rows_inf = 0
    with args.csv.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, skipinitialspace=False)
        header = next(reader)
        labels = [i for i, name in enumerate(header) if name.strip() == 'Label']
        if len(labels) != 1:
            raise ValueError(f'Coluna Label ambigua ou ausente: {labels}')
        label_index = labels[0]
        for row in reader:
            if not row:
                blank_records += 1
                continue
            if len(row) != len(header):
                raise ValueError(f'Largura incorreta na linha fisica {reader.line_num}')
            if row == header:
                raise ValueError(f'Cabecalho repetido na linha {reader.line_num}')
            n += 1
            label = row[label_index]
            classes[label] += 1
            if label not in examples:
                examples[label] = {'registro_dados': n, 'linha_fisica': reader.line_num,
                                   'valores': row}
            # Representacao injetiva dos campos: preserva grafia, espacos e rotulo.
            key = json.dumps(row, ensure_ascii=False, separators=(',', ':'))
            if key in seen:
                duplicates += 1
            seen.add(key)
            has_empty = has_nan = has_inf = False
            for i, value in enumerate(row):
                name = f'{i + 1}: {header[i]}'
                if not value.strip():
                    empty[name] += 1
                    has_empty = True
                    continue
                if i == label_index:
                    continue
                try:
                    number = float(value)
                except ValueError:
                    invalid[name] += 1
                    continue
                if math.isnan(number):
                    nan[name] += 1
                    has_nan = True
                elif math.isinf(number):
                    inf[name] += 1
                    has_inf = True
            rows_empty += has_empty
            rows_nan += has_nan
            rows_inf += has_inf
    assert sum(classes.values()) == n
    result = {
        'arquivo': args.csv.name, 'sha256': sha, 'bytes': args.csv.stat().st_size,
        'python': platform.python_version(), 'bibliotecas': 'somente biblioteca padrao',
        'linhas_dados': n, 'colunas': len(header), 'cabecalhos': header,
        'coluna_rotulo': header[label_index], 'contagens_rotulos_exatos': dict(classes),
        'rotulos_vazios_ou_so_espacos': sum(v for k, v in classes.items() if not k.strip()),
        'registros_vazios_sem_campos': blank_records,
        'campos_vazios_por_coluna': dict(empty), 'linhas_com_campo_vazio': rows_empty,
        'nan_por_coluna': dict(nan), 'linhas_com_nan': rows_nan,
        'infinitos_por_coluna': dict(inf), 'linhas_com_infinito': rows_inf,
        'nao_numericos_fora_rotulo': dict(invalid),
        'duplicatas_exatas_excedentes_primeira': duplicates,
        'registros_unicos_exatos': len(seen), 'exemplo_por_rotulo': examples,
    }
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('cabecalhos', 'exemplo_por_rotulo')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
