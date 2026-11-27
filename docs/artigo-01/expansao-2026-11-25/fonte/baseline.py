"""Baseline binário CPU: somente treino segunda-quarta e desempenho na quinta."""
import argparse
import hashlib
import json
import platform
import resource
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def gravar(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def ap_media(y, scores):
    """Average precision (degraus recall), agrupando todos os empates de score."""
    positivos = int(y.sum())
    if not positivos:
        return None
    ordem = np.argsort(-scores, kind="stable")
    s, t = scores[ordem], y[ordem]
    tp = np.cumsum(t, dtype=np.int64)
    fim = np.r_[np.flatnonzero(s[1:] != s[:-1]), len(s)-1]
    precisao = tp[fim] / (fim + 1)
    recall = tp[fim] / positivos
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precisao))


def metricas(y, scores, nominal, classes, limiar=0.5):
    pred = scores >= limiar
    cm = np.bincount(y.astype(np.int64)*2 + pred.astype(np.int64), minlength=4).reshape(2,2)
    (vn,fp),(fn,vp) = [[int(v) for v in row] for row in cm]
    p,n = vp+fn,vn+fp
    tipos = [{"tipo":nome,"suporte":int((nominal==i).sum()),"classe_binaria":int(i!=0),
        "recall_classe_binaria":float(np.mean(pred[nominal==i] == (i!=0))) if (nominal==i).any() else None}
        for i,nome in enumerate(classes)]
    return {"matriz_real_por_previsto":cm.tolist(),"ordem_classes":["BENIGN","ATTACK"],
        "suporte":{"BENIGN":n,"ATTACK":p},"limiar":limiar,
        "macro_f1":float((2*vn/(2*vn+fp+fn) + 2*vp/(2*vp+fp+fn))/2) if n and p else None,
        "precisao_ATTACK":vp/(vp+fp) if vp+fp else 0.0,
        "recall_ATTACK":vp/p if p else None,"FPR":fp/n if n else None,
        "PR_AUC_average_precision":ap_media(y,scores),
        "definicao_PR_AUC":"Average precision = soma(delta recall * precision) nos limiares distintos, empates agrupados; sem trapezios; positivo ATTACK",
        "recall_por_tipo_nominal":tipos}


@torch.inference_mode()
def prever(modelo,x):
    modelo.eval()
    return torch.cat([torch.sigmoid(modelo(torch.from_numpy(np.array(x[i:i+8192],copy=True))).squeeze(1))
                      for i in range(0,len(x),8192)]).numpy()


def dados_validacao(candidato):
    # Nenhum acesso a features/labels de sexta para predição ou desempenho.
    x=np.load(candidato/'dados/validacao_x_f32.npy',mmap_mode='r')
    y=np.load(candidato/'dados/validacao_y.npy',allow_pickle=False)
    nom=np.load(candidato/'dados/validacao_nominal.npy',allow_pickle=False)
    with np.load(candidato/'manifesto_indices_candidato.npz',allow_pickle=False) as a:
        mask=a['validacao_sensibilidade_raw64']
    classes=json.loads((candidato/'manifesto_candidato.json').read_text())['classes_nominais']
    return x,y,nom,mask,classes


def relatar_validacao(candidato,scores):
    _,y,nom,mask,classes=dados_validacao(candidato)
    return {"estado":"EXPLORATORIO; protocolo candidato; unica seed", "sexta_avaliada":False,
        "limiar_escolhido":"0.5 fixado antes do treino; sem calibracao na quinta",
        "principal":metricas(y,scores,nom,classes),
        "sensibilidade_raw64":metricas(y[mask],scores[mask],nom[mask],classes)}


def treinar(candidato,config,saida):
    inicio=time.monotonic()
    cfg=json.loads(config.read_text())
    assert cfg['modelo']=='regressao_logistica_torch' and cfg['epocas']==3 and cfg['limiar']==0.5
    saida.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True);torch.manual_seed(cfg['seed'])
    manifest=json.loads((candidato/'manifesto_candidato.json').read_text())
    assert manifest['estado']=='CANDIDATO_NAO_FINAL'
    for n in ['treino_x_f32.npy','treino_y.npy','validacao_x_f32.npy','validacao_y.npy']:
        assert sha(candidato/'dados'/n)==manifest['dados_hash']['dados/'+n]
    x=np.load(candidato/'dados/treino_x_f32.npy',mmap_mode='r')
    y=torch.from_numpy(np.load(candidato/'dados/treino_y.npy').astype(np.float32))
    modelo=nn.Linear(81,1)
    inicial=hashlib.sha256(b''.join(t.detach().numpy().tobytes() for t in modelo.state_dict().values())).hexdigest()
    configuracao={**cfg,'python':platform.python_version(),'pytorch':str(torch.__version__),'numpy':np.__version__,
        'manifesto_sha256':sha(candidato/'manifesto_candidato.json'),'preprocessamento_sha256':sha(candidato/'preprocessamento.npz'),
        'pesos_iniciais_sha256':inicial,'linhas_treino':len(y),'sexta_avaliada':False,
        'acessos_modelo':['dados/treino_x_f32.npy','dados/treino_y.npy','dados/validacao_x_f32.npy',
                         'dados/validacao_y.npy','dados/validacao_nominal.npy','mascara de validacao no NPZ']}
    gravar(saida/'configuracao_antes_treino.json',configuracao)
    opt=torch.optim.Adam(modelo.parameters(),lr=cfg['lr'],weight_decay=0.0)
    loss=nn.BCEWithLogitsLoss()
    historico=[];tempo_treino=time.monotonic()
    for epoca in range(1,cfg['epocas']+1):
        t=time.monotonic();soma=0.0;passos=0
        perm=torch.randperm(len(y),generator=torch.Generator().manual_seed(cfg['seed']+epoca))
        modelo.train()
        for idx in perm.split(cfg['lote']):
            xb=torch.from_numpy(np.array(x[idx.numpy()],copy=True))
            opt.zero_grad(set_to_none=True)
            l=loss(modelo(xb).squeeze(1),y[idx]);assert torch.isfinite(l)
            l.backward();opt.step();soma+=float(l.detach())*len(idx);passos+=1
        historico.append({'epoca':epoca,'BCE_online_ponderada':soma/len(y),'passos':passos,'tempo_s':time.monotonic()-t})
        print(historico[-1],flush=True)
    tempo_treino=time.monotonic()-tempo_treino
    with np.load(candidato/'preprocessamento.npz',allow_pickle=False) as a:
        checkpoint={'formato':'secfednet-logistica-candidato-ATTACK-v1','state_dict':modelo.state_dict(),
            'media':torch.from_numpy(a['media'].copy()),'escala':torch.from_numpy(a['escala'].copy()),
            'ordem_features':a['ordem_features'].tolist(),'classes':{'0':'BENIGN','1':'ATTACK'},'limiar':0.5,
            'configuracao':configuracao}
    torch.save(checkpoint,saida/'checkpoint.pt')
    xv,*_=dados_validacao(candidato)
    scores=prever(modelo,xv);np.save(saida/'scores_quinta.npy',scores)
    r=relatar_validacao(candidato,scores)
    r.update(tempo_treino_s=tempo_treino,tempo_total_s=time.monotonic()-inicio,
             pico_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_sha256=sha(saida/'checkpoint.pt'))
    gravar(saida/'historico.json',historico);gravar(saida/'validacao.json',r)
    print(json.dumps({k:v for k,v in r['principal'].items() if k!='recall_por_tipo_nominal'},indent=2),flush=True)


def verificar(candidato,saida):
    torch.set_num_threads(2)
    ck=torch.load(saida/'checkpoint.pt',map_location='cpu',weights_only=True)
    modelo=nn.Linear(81,1);modelo.load_state_dict(ck['state_dict'])
    xv,y,nom,mask,classes=dados_validacao(candidato)
    scores=prever(modelo,xv)
    assert np.array_equal(scores,np.load(saida/'scores_quinta.npy',allow_pickle=False))
    atual=relatar_validacao(candidato,scores);salvo=json.loads((saida/'validacao.json').read_text())
    assert atual['principal']==salvo['principal'] and atual['sensibilidade_raw64']==salvo['sensibilidade_raw64']
    # Um exemplo bruto de quinta também confirma o encadeamento de pré-processamento.
    bruto=np.load(candidato/'dados/validacao_bruto_f64.npy',mmap_mode='r')[0]
    transformado=((torch.tensor(bruto.copy(),dtype=torch.float64)-ck['media'])/ck['escala']).float().numpy()
    assert np.array_equal(transformado,xv[0])
    gravar(saida/'verificacao_recarga.json',{'status':'OK','weights_only':True,'dispositivo':'cpu',
        'scores_quinta_bit_a_bit':True,'metricas_principal_sensibilidade_identicas':True,
        'exemplo_bruto_quinta_preprocessado_igual':True,'sexta_avaliada':False})
    print('RECARREGAMENTO E VALIDACAO: OK',flush=True)


def testar():
    assert abs(ap_media(np.array([0,1,1,0]),np.array([.4,.3,.2,.1]))-7/12)<1e-12
    assert ap_media(np.array([0,1]),np.array([.5,.5]))==.5
    m=metricas(np.array([0,1]),np.array([.5,.5]),np.array([0,1]),['BENIGN','A'])
    assert m['matriz_real_por_previsto']==[[0,1],[0,1]] and abs(m['macro_f1']-1/3)<1e-12
    assert m['FPR']==1 and m['recall_ATTACK']==1 and m['precisao_ATTACK']==.5
    print('TESTES METRICAS: OK')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='modo',required=True)
    a=s.add_parser('treinar');a.add_argument('candidato',type=Path);a.add_argument('config',type=Path);a.add_argument('saida',type=Path)
    a=s.add_parser('verificar');a.add_argument('candidato',type=Path);a.add_argument('saida',type=Path)
    s.add_parser('testar');a=p.parse_args()
    if a.modo=='treinar':treinar(a.candidato,a.config,a.saida)
    elif a.modo=='verificar':verificar(a.candidato,a.saida)
    else:testar()
