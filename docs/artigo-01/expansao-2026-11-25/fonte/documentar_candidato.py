"""Exporta parâmetros e colisões incrementais, sem treino ou alteração de máscaras."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from preparar_candidato import colisao_adicional
from fontes.auditar_split import tabela


def executar(c):
    with np.load(c/'preprocessamento.npz',allow_pickle=False) as p:
        nomes=p['ordem_features'].tolist();media=p['media'];escala=p['escala']
    j=json.loads((c/'manifesto_candidato.json').read_text());const=j['preprocessamento']['colunas_constantes']
    tabela(c/'preprocessamento_por_feature.csv',[{'posicao0':i,'feature':n,'media_treino_f64':float(media[i]),
        'desvio_treino_ddof0':0.0 if i in const else float(escala[i]),'escala_efetiva_f64':float(escala[i]),
        'constante_no_treino':i in const} for i,n in enumerate(nomes)])
    rows=[]
    with np.load(c/'manifesto_indices_candidato.npz',allow_pickle=False) as a:
        for scenario in ['principal','sensibilidade_raw64']:
            ds=[]
            for s in ['treino','validacao','teste']:
                keep=a[s+'_'+scenario]
                # A referência desta chamada é normalizado64, não vetor bruto.
                ds.append({'vetor_float64':a[s+'_norm64_code'][keep], 'modelo_float32':a[s+'_modelo32_code'][keep]})
            for i,k in [(0,1),(0,2),(1,2)]:
                va,vb=ds[i]['modelo_float32'],ds[k]['modelo_float32']
                u=np.intersect1d(va,vb);ma,mb=np.isin(va,u),np.isin(vb,u)
                rows.append({'cenario':scenario,'par':f'{["treino","validacao","teste"][i]}_x_{["treino","validacao","teste"][k]}',
                    'referencia':'normalizado_float64','representacao':'modelo_float32',
                    **colisao_adicional(ds[i],ds[k],'modelo_float32',ma,mb)})
    tabela(c/'colisoes_incrementais_float32.csv',rows)
    # Casos mínimos: duas fontes diferentes colapsam; fontes iguais não são adicionais.
    a={'vetor_float64':np.array([0]),'norm':np.array([0])}
    b={'vetor_float64':np.array([1,1]),'norm':np.array([0,0])}
    r=colisao_adicional(a,b,'norm',np.array([True]),np.array([True,True]))
    assert r=={'chaves_com_colisao_adicional':1,'linhas_a_colisao_adicional':1,
               'linhas_b_colisao_adicional':2,'pares_adicionais_raw_diferente':2}
    b['vetor_float64'][:]=0
    assert colisao_adicional(a,b,'norm',np.array([True]),np.array([True,True]))['pares_adicionais_raw_diferente']==0
    x=np.array([1.,np.nextafter(1.,2.)]);assert x[0]!=x[1] and x.astype(np.float32)[0]==x.astype(np.float32)[1]
    assert ((x-1e20)/1e20)[0]==((x-1e20)/1e20)[1]
    (c/'teste_colisoes.json').write_text(json.dumps({'status':'OK','casos':['colisao nova versus fonte igual',
        'multiplicidade de linhas e pares','colapso float64 por subtracao/escala','colapso adicional na conversao float32']},ensure_ascii=False,indent=2)+'\n')
    print('PARÂMETROS, COLISÕES INCREMENTAIS E TESTES: OK')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidato',type=Path);a=p.parse_args();executar(a.candidato)
