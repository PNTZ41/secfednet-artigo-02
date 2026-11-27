"""Par CNN central/FedAvg, quinta somente, processo único com dois threads Torch."""
import argparse
import hashlib
import json
import math
import random
import resource
import sys
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
from torch import nn

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'fonte'))
sys.path.insert(0,str(ROOT/'fonte/fontes'))
import treinar_cnn as original
from baseline import dados_validacao,relatar_validacao,sha


def salvar(p,x):
    q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');q.replace(p)


def peso_hash(m):
    return hashlib.sha256(b''.join(t.detach().cpu().numpy().tobytes() for t in m.state_dict().values())).hexdigest()


@torch.inference_mode()
def prever(m,x):
    m.eval()
    return torch.cat([torch.sigmoid(m(torch.from_numpy(np.array(x[i:i+512],copy=True)))[0])
                      for i in range(0,len(x),512)]).numpy()


def executar(seed,metodo):
    inicio=time.monotonic();cfg=json.loads((ROOT/'controle/config.json').read_text())
    assert original.LOTE==cfg['lote']==512 and original.TAXA==cfg['lr']==0.001
    candidato=ROOT/'reproducao/candidato';out=ROOT/'comparacao'/f'seed-{seed}'/metodo
    out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    random.seed(seed);torch.manual_seed(seed)
    x=np.load(candidato/'dados/treino_x_f32.npy',mmap_mode='r');y=np.load(candidato/'dados/treino_y.npy',allow_pickle=False)
    with patch.object(original.piloto,'CLIENTES',5),patch.object(original.piloto,'CLASSES',('BENIGN','ATTACK')):
        partes,tentativa=original.distribuir_dirichlet(y,cfg['particao_seed'][str(seed)])
    assert np.array_equal(np.sort(np.concatenate(partes)),np.arange(len(y)))
    np.savez_compressed(out/'particao.npz',**{f'cliente_{i}':a for i,a in enumerate(partes)})
    cont=[{'cliente':i,'total':len(idx),'BENIGN':int((y[idx]==0).sum()),'ATTACK':int((y[idx]==1).sum())}
          for i,idx in enumerate(partes)]
    modelo=original.CNN1D();inicial=peso_hash(modelo);torch.save(modelo.state_dict(),out/'inicial.pt')
    config={**cfg,'seed':seed,'metodo':metodo,'pesos_iniciais_sha256':inicial,'particao':cont,'tentativa':tentativa,
        'particao_npz_sha256':sha(out/'particao.npz'),'manifesto_candidato_sha256':sha(candidato/'manifesto_candidato.json'),
        'mascaras_validacao_sha256':sha(candidato/'manifesto_indices_candidato.npz'),
        'arquitetura_sha256':sha(ROOT/'fonte/fontes/cnn1d.py'),'python':sys.version.split()[0],
        'pytorch':str(torch.__version__),'flower':str(original.flwr.__version__),'numpy':np.__version__,'sexta_avaliada':False}
    salvar(out/'configuracao_antes_treino.json',config)
    passos=[0];old_step=torch.optim.Adam.step
    def contar(opt,*args,**kwargs):
        assert opt.defaults['lr']==cfg['lr'] and opt.defaults['betas']==tuple(cfg['betas'])
        assert opt.defaults['eps']==cfg['eps'] and opt.defaults['weight_decay']==0 and not opt.defaults['amsgrad']
        passos[0]+=1
        return old_step(opt,*args,**kwargs)
    hist=[];eventos=[];t0=time.monotonic()
    with patch.object(torch.optim.Adam,'step',contar):
        if metodo=='central':
            yt=torch.from_numpy(y.astype(np.float32));loss=nn.BCEWithLogitsLoss()
            for epoca in range(1,6):
                modelo.train();t=time.monotonic();soma=0.;antes=passos[0]
                # Mesma política de reinício de estado por unidade época/rodada.
                opt=torch.optim.Adam(modelo.parameters(),lr=cfg['lr'],betas=tuple(cfg['betas']),
                    eps=cfg['eps'],weight_decay=0.0,amsgrad=False)
                perm=torch.randperm(len(y),generator=torch.Generator().manual_seed(seed+100*epoca))
                for idx in perm.split(cfg['lote']):
                    xb=torch.from_numpy(np.array(x[idx.numpy()],copy=True));opt.zero_grad(set_to_none=True)
                    logits,_=modelo(xb);l=loss(logits,yt[idx]);assert torch.isfinite(l)
                    l.backward();opt.step();soma+=float(l.detach())*len(idx)
                hist.append({'epoca':epoca,'BCE_online':soma/len(y),'passos':passos[0]-antes,'exposicoes':len(y),'tempo_s':time.monotonic()-t})
                salvar(out/'historico.json',hist);salvar(out/'progresso.json',{'seed':seed,'metodo':metodo,'epoca_concluida':epoca,'passos':passos[0]})
                print(seed,metodo,hist[-1],flush=True)
            esperados=5*math.ceil(len(y)/512)
        else:
            fit=original.ClienteCNN.fit
            def observado(cliente,parametros,c):
                antes=passos[0];ret=fit(cliente,parametros,c)
                e={'rodada':int(c['rodada']),'cliente':cliente.numero,'exemplos':ret[1],'passos':passos[0]-antes}
                assert e['passos']==math.ceil(ret[1]/512)
                eventos.append(e);salvar(out/'eventos_clientes.json',eventos);salvar(out/'progresso.json',{'seed':seed,'metodo':metodo,'ultimo_fit_concluido':e,'passos':passos[0]})
                print(seed,metodo,e,flush=True)
                return ret
            with patch.object(original,'SEED_MODELO',seed),patch.object(original.ClienteCNN,'fit',observado):
                hist=original.rodar_flower(modelo,x,y,partes,5)
            assert len(eventos)==25 and sum(e['exemplos'] for e in eventos)==5*len(y)
            esperados=5*sum(math.ceil(len(a)/512) for a in partes)
        assert passos[0]==esperados
    treino_s=time.monotonic()-t0
    with np.load(candidato/'preprocessamento.npz',allow_pickle=False) as p:
        ck={'formato':'CNN-candidato-ATTACK-5-v1','state_dict':modelo.state_dict(),
            'media':torch.from_numpy(p['media'].copy()),'escala':torch.from_numpy(p['escala'].copy()),
            'classes':{'0':'BENIGN','1':'ATTACK'},'ordem_features':p['ordem_features'].tolist(),'limiar':0.5,'configuracao':config}
    torch.save(ck,out/'checkpoint.pt')
    xv,*_=dados_validacao(candidato);s=prever(modelo,xv);np.save(out/'scores_quinta.npy',s)
    # Recarga segura; a reprodução anterior já conferiu também em processo independente.
    rec=torch.load(out/'checkpoint.pt',map_location='cpu',weights_only=True)
    m=original.CNN1D();m.load_state_dict(rec['state_dict']);assert np.array_equal(prever(m,xv),s)
    metric=relatar_validacao(candidato,s)
    result={'seed':seed,'metodo':metodo,'metricas':metric,'passos_otimizador':passos[0],
        'exposicoes_exemplos':5*len(y),'tempo_treino_s':treino_s,'tempo_total_s':time.monotonic()-inicio,
        'pico_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'pesos_iniciais_sha256':inicial,
        'pesos_finais_sha256':peso_hash(modelo),'checkpoint_sha256':sha(out/'checkpoint.pt'),
        'recarga_weights_only_cpu_scores_iguais':True,'sexta_avaliada':False}
    salvar(out/'resultado.json',result);salvar(out/'progresso.json',{'status':'concluido','seed':seed,'metodo':metodo})
    print('MODELO CONCLUIDO',seed,metodo,'passos',passos[0],'exposicoes',5*len(y),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('seed',type=int,choices=[23,41,89]);p.add_argument('metodo',choices=['central','fedavg'])
    a=p.parse_args();executar(a.seed,a.metodo)
