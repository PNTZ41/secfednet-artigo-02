"""Uma rodada CNN/Flower como integração, sem comparação científica ou teste sexta."""
import argparse
import json
import random
import resource
import sys
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

RAIZ=Path(__file__).resolve().parent
sys.path.insert(0,str(RAIZ/'fontes'))
import treinar_cnn as original
from baseline import gravar,sha,dados_validacao,relatar_validacao


@torch.inference_mode()
def scores(modelo,x):
    modelo.eval()
    return torch.cat([torch.sigmoid(modelo(torch.from_numpy(np.array(x[i:i+512],copy=True)))[0])
                      for i in range(0,len(x),512)]).numpy()


def treinar(candidato,saida):
    inicio=time.monotonic();saida.mkdir(parents=True,exist_ok=False)
    random.seed(23);torch.manual_seed(23);torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    x=np.load(candidato/'dados/treino_x_f32.npy',mmap_mode='r')
    y=np.load(candidato/'dados/treino_y.npy',allow_pickle=False)
    with patch.object(original.piloto,'CLIENTES',5),patch.object(original.piloto,'CLASSES',('BENIGN','ATTACK')):
        partes,tentativa=original.distribuir_dirichlet(y,2305)
    assert np.array_equal(np.sort(np.concatenate(partes)),np.arange(len(y)))
    part=[{'cliente':i,'total':len(idx),'BENIGN':int((y[idx]==0).sum()),'ATTACK':int((y[idx]==1).sum())}
          for i,idx in enumerate(partes)]
    cfg={'uso':'VERIFICACAO_DE_INTEGRACAO; sem conclusao comparativa','modelo':'CNN1D original; novo contrato ATTACK',
        'rodadas':1,'clientes':5,'epocas_locais':1,'lote':512,'otimizador':'Adam reiniciado por fit','lr':0.001,
        'agregacao':'ponderada por numero de exemplos, CID ordenado, inplace=False','seed_modelo':23,
        'seed_particao':2305,'alpha':0.5,'tentativa_aceita':tentativa,'seed_minibatches':'23+100*rodada+cliente',
        'particao':part,'limiar':0.5,'ajuste_na_quinta':False,'sexta_avaliada':False,
        'manifesto_sha256':sha(candidato/'manifesto_candidato.json'),
        'python':sys.version.split()[0],'pytorch':str(torch.__version__),'flower':str(original.flwr.__version__),
        'fonte_rodar_flower_sha256':sha(RAIZ/'fontes/treinar_cnn.py')}
    gravar(saida/'configuracao_antes_treino.json',cfg)
    np.savez_compressed(saida/'clientes_treino_idx0.npz',**{f'cliente_{i}':v for i,v in enumerate(partes)})
    modelo=original.CNN1D();t=time.monotonic()
    hist=original.rodar_flower(modelo,x,y,partes,1)
    tempo_treino=time.monotonic()-t
    with np.load(candidato/'preprocessamento.npz',allow_pickle=False) as p:
        checkpoint={'formato':'secfednet-cnn1d-candidato-ATTACK-integracao-v1','state_dict':modelo.state_dict(),
            'media':torch.from_numpy(p['media'].copy()),'escala':torch.from_numpy(p['escala'].copy()),
            'ordem_features':p['ordem_features'].tolist(),'classes':{'0':'BENIGN','1':'ATTACK'},'limiar':0.5,'configuracao':cfg}
    torch.save(checkpoint,saida/'checkpoint.pt')
    xv,*_=dados_validacao(candidato);s=scores(modelo,xv);np.save(saida/'scores_quinta.npy',s)
    r=relatar_validacao(candidato,s)
    r.update(uso='INTEGRACAO; arquitetura e orcamento diferentes do baseline, sem comparacao conclusiva',
             historico_flower=hist,tempo_treino_s=tempo_treino,tempo_total_s=time.monotonic()-inicio,
             pico_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_sha256=sha(saida/'checkpoint.pt'))
    gravar(saida/'validacao_integracao.json',r)
    gravar(saida/'volume_parametros.json',{'rodada':1,'participantes':list(range(5)),'exemplos':len(y),
        'bytes_brutos_parametros_enviados':5*sum(t.numel()*t.element_size() for t in modelo.state_dict().values()),
        'bytes_brutos_parametros_recebidos':5*sum(t.numel()*t.element_size() for t in modelo.state_dict().values()),
        'escopo':'arrays float32 da simulacao em processo, sem serializacao ou transporte'})
    print('INTEGRACAO FLOWER CONCLUIDA',flush=True)


def verificar(candidato,saida):
    torch.set_num_threads(2)
    c=torch.load(saida/'checkpoint.pt',map_location='cpu',weights_only=True)
    m=original.CNN1D();m.load_state_dict(c['state_dict'])
    x,*_=dados_validacao(candidato);s=scores(m,x)
    assert np.array_equal(s,np.load(saida/'scores_quinta.npy',allow_pickle=False))
    r=relatar_validacao(candidato,s);prev=json.loads((saida/'validacao_integracao.json').read_text())
    assert r['principal']==prev['principal'] and r['sensibilidade_raw64']==prev['sensibilidade_raw64']
    gravar(saida/'verificacao_recarga.json',{'status':'OK','weights_only':True,'CPU':True,
        'scores_quinta_bit_a_bit':True,'sexta_avaliada':False})
    print('RECARREGAMENTO FLOWER: OK',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('modo',choices=['treinar','verificar'])
    p.add_argument('candidato',type=Path);p.add_argument('saida',type=Path);a=p.parse_args()
    (treinar if a.modo=='treinar' else verificar)(a.candidato,a.saida)
