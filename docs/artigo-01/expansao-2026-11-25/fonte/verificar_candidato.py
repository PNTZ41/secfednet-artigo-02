"""Confere candidato/máscaras/parâmetros/representações, sem desempenho de sexta."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def executar(c):
    j=json.loads((c/'manifesto_candidato.json').read_text())
    assert j['estado']=='CANDIDATO_NAO_FINAL' and j['classes']=={'0':'BENIGN','1':'ATTACK'}
    assert sha(c/'manifesto_indices_candidato.npz')==j['indices_sha256']
    assert sha(c/'preprocessamento.npz')==j['preprocessamento_sha256']
    for nome,h in j['dados_hash'].items():assert sha(c/nome)==h,nome
    with np.load(c/'preprocessamento.npz',allow_pickle=False) as p:
        media,escala=p['media'],p['escala']
        assert media.dtype==escala.dtype==np.float64 and len(media)==len(escala)==81
        assert p['ordem_features'].tolist()==j['ordem_features']
    with np.load(c/'manifesto_indices_candidato.npz',allow_pickle=False) as a:
        previous=np.array([],dtype=np.int64)
        for s in ['treino','validacao','teste']:
            raw=a[s+'_raw_code'];mask=a[s+'_sensibilidade_raw64']
            assert len(raw)==j['principal'][s] and int(mask.sum())==j['sensibilidade_raw64'][s]
            assert np.array_equal(mask,~np.isin(raw,previous))
            previous=np.union1d(previous,raw)
            assert a[s+'_principal'].all()
            nom=a[s+'_rotulo_nominal_idx0'];y=a[s+'_y_binario']
            assert np.array_equal(y,(nom!=0).astype(np.uint8))
            for dia in np.unique(a[s+'_captura_idx0']):
                regs=a[s+'_csv_registro1'][a[s+'_captura_idx0']==dia]
                assert np.all(np.diff(regs)>0) and regs.min()>=1
            xr=np.load(c/f'dados/{s}_bruto_f64.npy',mmap_mode='r')
            xm=np.load(c/f'dados/{s}_x_f32.npy',mmap_mode='r')
            assert xm.dtype==np.float32
            for i in range(0,len(xr),32768):
                z=((xr[i:i+32768]-media)/escala).astype(np.float32)
                assert np.isfinite(z).all() and np.array_equal(z,xm[i:i+32768])
        for i,s in enumerate(['treino','validacao','teste']):
            for t in ['treino','validacao','teste'][i+1:]:
                assert not np.intersect1d(a[s+'_raw_code'][a[s+'_sensibilidade_raw64']],
                                        a[t+'_raw_code'][a[t+'_sensibilidade_raw64']]).size
    # Reconciliacao por tipo com a auditoria original, descontando só qualidade.
    ref=Path(__file__).resolve().parent/'auditoria_referencia/simulacoes_por_classe.csv'
    with ref.open() as f:old=list(csv.DictReader(f))
    with (c/'impacto_sensibilidade_por_tipo.csv').open() as f:impact=list(csv.DictReader(f))
    for r in impact:
        q={'treino':4,'validacao':1,'teste':0}[r['conjunto']] if r['tipo']=='BENIGN' else 0
        prev=next(x for x in old if x['cenario']=='sequencial_vetor_float64' and x['escala']=='nominal'
                  and x['conjunto']==r['conjunto'] and x['classe']==r['tipo'])
        assert int(r['principal'])==int(prev['antes'])-q
        assert int(r['sensibilidade'])==int(prev['depois'])-q
    return {'status':'OK','estado':'CANDIDATO_NAO_FINAL','hashes_dados_conferidos':len(j['dados_hash']),
        'mascaras_reconciliadas_com_auditoria':True,'representacao_float32_verificada_todos_registros':True,
        'sexta':'somente verificacao de arrays/mascaras/intersecoes; nenhuma previsao ou metrica de desempenho'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidato',type=Path);a=p.parse_args()
    print(json.dumps(executar(a.candidato),ensure_ascii=False,indent=2))
