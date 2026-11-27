"""Gate numérico estrito da reprodução VM contra a referência do Kubuntu."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def executar(root):
    ref=json.loads((root/'controle/referencia_kubuntu.json').read_text())
    novo=root/'reproducao';campos=[];documentais=[]
    def check(nome,a,b):
        igual=a==b;campos.append({'campo':nome,'igual':igual,**({} if igual else {'kubuntu':a,'vm':b})})
    def arr(nome,a,esperado):
        check(nome+'/shape',list(a.shape),esperado['shape'])
        check(nome+'/dtype',str(a.dtype),esperado['dtype'])
        h=hashlib.sha256(a.tobytes()).hexdigest();check(nome+'/sha256',h,esperado['sha256'])
        if h!=esperado['sha256'] and esperado['valores'] is not None and a.dtype.kind in 'fiu':
            e=np.asarray(esperado['valores']).reshape(esperado['shape'])
            campos.append({'campo':nome+'/delta','igual':False,'max_delta':float(np.max(np.abs(a.astype(float)-e)))})
    manifest=json.loads((novo/'candidato/manifesto_candidato.json').read_text())
    for k in ['estado','classes','zip_sha256','arquivos','ordem_features','classes_nominais','principal',
              'sensibilidade_raw64','indice_semantica','capturas_ordem','ordem_linhas','preprocessamento',
              'indices_sha256','preprocessamento_sha256']:
        check('manifesto/'+k,manifest[k],ref['manifesto'][k])
    for tipo,nome in [('indices','manifesto_indices_candidato.npz'),('preprocessamento','preprocessamento.npz')]:
        with np.load(novo/'candidato'/nome,allow_pickle=False) as a:
            check(tipo+'/chaves',sorted(a.files),sorted(ref[tipo]))
            for k in a.files:arr(tipo+'/'+k,a[k],ref[tipo][k])
    for n,h in ref['manifesto']['dados_hash'].items():check('matriz/'+n,sha(novo/'candidato'/n),h)
    for metodo,arquivo in [('baseline','validacao.json'),('fedavg_integracao','validacao_integracao.json')]:
        e=ref['modelos'][metodo];p=novo/metodo
        c=torch.load(p/'checkpoint.pt',map_location='cpu',weights_only=True)
        for k,t in c['state_dict'].items():arr(metodo+'/state_dict/'+k,t.numpy(),e['state_dict'][k])
        for k in ['media','escala']:arr(metodo+'/'+k,c[k].numpy(),ref['preprocessamento'][k])
        v=json.loads((p/arquivo).read_text());check(metodo+'/sexta_avaliada',v['sexta_avaliada'],False)
        for s in ['principal','sensibilidade_raw64']:check(metodo+'/metricas/'+s,v[s],e['metricas'][s])
        check(metodo+'/scores_quinta_sha256',sha(p/'scores_quinta.npy'),e['scores_quinta_sha256'])
        rec=json.loads((p/'verificacao_recarga.json').read_text());check(metodo+'/recarga',rec['status'],'OK')
        cfg=json.loads((p/'configuracao_antes_treino.json').read_text())
        for k,valor in e['configuracao'].items():
            if k == 'manifesto_sha256':
                if cfg[k]!=valor:documentais.append({'campo':metodo+'/config/'+k,'kubuntu':valor,'vm':cfg[k],
                    'motivo':'vinculo ao manifesto que inclui tempo/pico da execucao; parametros numericos comparados separadamente'})
            else:check(metodo+'/config/'+k,cfg[k],valor)
        if sha(p/'checkpoint.pt')!=e['checkpoint_sha256']:
            documentais.append({'campo':metodo+'/checkpoint_sha256','kubuntu':e['checkpoint_sha256'],
                'vm':sha(p/'checkpoint.pt'),'motivo':'checkpoint inclui configuracao e hash do manifesto especifico da execucao; pesos/normalizacao conferidos campo a campo'})
        documentais.append({'campo':metodo+'/tempos_pico','vm':{k:v[k] for k in ['tempo_treino_s','tempo_total_s','pico_rss_kib']},
                            'motivo':'medidas de execucao/ambiente, nao criterios de igualdade numerica'})
    result={'passou':all(c['igual'] for c in campos),'tolerancia':0.0,'campos':campos,'diferencas_documentais':documentais,
            'criterio':'indices, contagens, parametros, matrizes, pesos e scores/metricas da quinta exatos; recargas OK',
            'sexta_desempenho':False}
    (root/'comparacao_reproducao.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('GATE REPRODUCAO:',result['passou'],'campos',len(campos),flush=True)
    if not result['passou']:raise SystemExit(2)


if __name__=='__main__':executar(Path(sys.argv[1]))
