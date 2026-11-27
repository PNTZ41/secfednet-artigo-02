"""Valida seleção fechada, links e tabelas sem dataset, treino ou dependências externas."""
import csv
import hashlib
import json
import math
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(name):
    return json.loads((ROOT / name).read_text())


def rows(name):
    with (ROOT / name).open(newline='') as f:
        return list(csv.DictReader(f))


def same(a, b):
    assert math.isclose(float(a), float(b), abs_tol=1e-12, rel_tol=0), (a, b)


def main():
    manifest = {}
    for line in (ROOT / 'SHA256_EXPERIMENTOS').read_text().splitlines():
        h, n = line.split(maxsplit=1)
        p = Path(n)
        assert not p.is_absolute() and '..' not in p.parts and n not in manifest
        assert len(h) == 64 and all(c in '0123456789abcdef' for c in h)
        assert sha(ROOT / n) == h, n
        manifest[n] = h
    found = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}
    assert found == set(manifest) | {'SHA256_EXPERIMENTOS'}, 'Manifesto não fecha seleção'
    assert found == set((ROOT / 'LISTA_ARQUIVOS.txt').read_text().splitlines())
    for r in read('PROVENIENCIA.json')['copias']:
        assert sha(ROOT / r['entrega']) == r['sha256_entrega'], r['entrega']
    # Manifestações históricas da VM referem-se aos bytes antes da edição LF/links.
    provenance = {r['entrega']: r for r in read('PROVENIENCIA.json')['copias']}
    for name in ['RETORNO_VM', 'ENTREGA_LOCAL']:
        for line in (ROOT / ('historicos/vm_SHA256_' + name)).read_text().splitlines():
            h, n = line.split(maxsplit=1)
            if n == 'SHA256_RETORNO_VM':
                assert sha(ROOT / 'historicos/vm_SHA256_RETORNO_VM') == h
            else:
                assert provenance['vm/' + n]['sha256_origem'] == h, n
    links = 0
    for p in ROOT.rglob('*.md'):
        text = p.read_text()
        assert '{l(' not in text, p
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if target.startswith(('https://', 'http://', 'mailto:', '#')):
                continue
            q = (p.parent / target.split('#')[0]).resolve()
            assert q.is_relative_to(ROOT.parents[2]) and q.exists(), (str(p), target)
            links += 1
    j = read('candidato/manifesto_candidato.json')
    contract = read('fonte/contrato_candidato.json')
    assert j['estado'] == contract['estado'] == 'CANDIDATO_NAO_FINAL'
    assert j['classes'] == contract['classes'] == {'0': 'BENIGN', '1': 'ATTACK'}
    assert j['ordem_features'] == contract['ordem_features']
    assert len(set(j['ordem_features'])) == 81
    assert j['principal'] == {'treino': 1184424, 'validacao': 360078, 'teste': 543490}
    assert j['sensibilidade_raw64'] == {'treino': 1184424, 'validacao': 328429, 'teste': 429801}
    scaler = rows('candidato/preprocessamento_por_feature.csv')
    assert [r['feature'] for r in scaler] == j['ordem_features']
    assert [int(r['posicao0']) for r in scaler] == list(range(81))
    for r in scaler:
        assert math.isfinite(float(r['media_treino_f64'])) and float(r['escala_efetiva_f64']) > 0
    checks = rows('vm/tabelas/reproducao_checks.csv')
    assert len(checks) == 231 and all(r['igual'] == 'True' for r in checks)
    results = rows('vm/tabelas/resultados_por_seed.csv')
    assert len(results) == 12
    assert len({(r['seed'], r['metodo'], r['cenario']) for r in results}) == 12
    nominal = rows('vm/tabelas/recall_por_tipo.csv')
    assert len(nominal) == 192
    for r in results:
        tn, fp, fn, tp = (int(r[n]) for n in ['VN', 'FP', 'FN', 'VP'])
        assert tn + fp == int(r['suporte_BENIGN'])
        assert fn + tp == int(r['suporte_ATTACK']) == 71907
        assert tn + fp == (288171 if r['cenario'] == 'principal' else 256522)
        same(r['FPR'], fp / (tn + fp))
        same(r['recall_ATTACK'], tp / (fn + tp))
        same(r['precisao_ATTACK'], tp / (tp + fp))
        same(r['macro_F1'], (2 * tn / (2 * tn + fp + fn) + 2 * tp / (2 * tp + fp + fn)) / 2)
        assert 0 <= float(r['AP']) <= 1
        types = [n for n in nominal if all(n[k] == r[k] for k in ['seed', 'metodo', 'cenario'])]
        assert len(types) == 16
        assert sum(int(n['suporte']) for n in types) == tn + fp + fn + tp
        benign = next(n for n in types if n['tipo'] == 'BENIGN')
        assert int(benign['suporte']) == tn + fp
        same(benign['recall_classe_binaria'], tn / (tn + fp))
        positives = [n for n in types if n['tipo'] != 'BENIGN']
        assert sum(int(n['suporte']) for n in positives) == fn + tp
        weighted = 0
        for n in positives:
            support = int(n['suporte'])
            if support:
                weighted += support * float(n['recall_classe_binaria'])
            else:
                assert n['recall_classe_binaria'] == 'NA'
        same(weighted / (fn + tp), tp / (fn + tp))
    variation = rows('vm/tabelas/variacao_entre_seeds.csv')
    assert len(variation) == 20
    for r in variation:
        vals = [float(x[r['metrica']]) for x in results
                if x['metodo'] == r['metodo'] and x['cenario'] == r['cenario']]
        assert len(vals) == int(r['n_seeds']) == 3
        for name, value in [('media', statistics.mean(vals)), ('desvio_amostral_ddof1', statistics.stdev(vals)),
                            ('minimo', min(vals)), ('maximo', max(vals))]:
            same(r[name], value)
    budgets = rows('vm/tabelas/orcamento_por_seed.csv')
    assert len(budgets) == 6
    for seed in ['23', '41', '89']:
        pair = [r for r in budgets if r['seed'] == seed]
        assert len(pair) == 2 and {r['metodo'] for r in pair} == {'central', 'fedavg'}
        for key in ['pesos_iniciais_sha256', 'particao_sha256', 'mascaras_sha256']:
            assert pair[0][key] == pair[1][key]
        for r in pair:
            assert int(r['exposicoes']) == 5922120
            expected = 11570 if r['metodo'] == 'central' else (11575 if seed == '89' else 11580)
            assert int(r['passos_otimizador']) == expected
    vm = read('vm/manifesto_execucao.json')
    assert vm['sexta_desempenho'] is False and vm['status']['estado'] == 'concluida'
    # Não confunde ausência de scores com novo cálculo independente de AP.
    print(json.dumps({'status': 'OK', 'arquivos': len(found), 'hashes': len(manifest), 'links_locais': links,
                      'checks_VM': 231, 'matrizes': 12, 'nominais': 192, 'variacoes_recalculadas': 20,
                      'pares_configuracao': 3,
                      'limite': 'AP preservada dos ensaios, não recalculada sem scores. Sem desempenho na sexta.'},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
