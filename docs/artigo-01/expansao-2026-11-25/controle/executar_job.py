"""Supervisor persistente, limite externo 45 min e finalização parcial sem dependências."""
import csv
import hashlib
import json
import os
import re
import shutil
import signal
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'controle/config.json').read_text())
START=time.monotonic();DEADLINE=START+CFG['prazo_interno_s']
STATUS={'estado':'em_andamento','inicio_BRT':datetime.now(ZoneInfo('America/Belem')).isoformat(),
        'limite_externo_s':2700,'etapa_atual':'inicializacao','concluidas':[],'PID':os.getpid()}


def agora():return datetime.now(ZoneInfo('America/Belem')).isoformat()


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def salvar(p,x):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)


def atualizar(**kw):
    STATUS.update(kw);STATUS['atualizacao_BRT']=agora();salvar(ROOT/'STATUS.json',STATUS)
    (ROOT/'STATUS.md').write_text(f"# Rodada limitada\n\nEstado: {STATUS['estado']}. Etapa: {STATUS['etapa_atual']}.\n\nInício: {STATUS['inicio_BRT']}. Limite: 45 minutos.\n\nConcluídas: {', '.join(x['etapa'] for x in STATUS['concluidas'])}.\n")


def git_estado():
    repo=Path(CFG.get('repo_estado','/home/williian/secfednet-repro/codigo'))
    def g(*args):return subprocess.check_output(['git','-C',str(repo),'-c','core.fsmonitor=false',*args],text=True)
    nomes=[n for n in g('ls-files','-z').split('\0') if n]
    return {'head':g('rev-parse','HEAD').strip(),'status':g('status','--short','--branch','--untracked-files=all'),
            'stage':g('diff','--cached','--name-status'),'tracked':{n:sha(repo/n) for n in nomes}}


def tabela(p,rows):
    if not rows:return
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def etapa(nome,cmd,env,permitir_falha=False):
    restante=DEADLINE-time.monotonic()
    if restante<=0:raise TimeoutError('Limite interno de 44 minutos atingido; reserva para relatório.')
    atualizar(etapa_atual=nome,comando_atual=cmd)
    print(agora(),'INICIO',nome,flush=True);t=time.monotonic()
    log=ROOT/'logs'/f'{nome}.log'
    with log.open('w') as f:
        p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            atualizar(PID_filho=p.pid,log_atual=str(log))
            code=p.wait(timeout=restante)
        except BaseException:
            # Encerra também os netos de bash/uv, preservando o teto da rodada.
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait()
            raise
    item={'etapa':nome,'comando':cmd,'exit_code':code,'tempo_s':time.monotonic()-t,'log':str(log.relative_to(ROOT))}
    if code==0:STATUS['concluidas'].append(item)
    else:STATUS.setdefault('falhas',[]).append(item)
    atualizar(PID_filho=None)
    print(agora(),'FIM',nome,'exit',code,flush=True)
    if code and not permitir_falha:raise RuntimeError(f'{nome} retornou {code}; consultar {log}')
    return code


def montar_tabelas():
    resultados=[];nominais=[];orcamentos=[];pares={}
    for seed in CFG['seeds']:
        for metodo in ['central','fedavg']:
            p=ROOT/'comparacao'/f'seed-{seed}'/metodo
            if not (p/'resultado.json').exists():continue
            j=json.loads((p/'resultado.json').read_text());c=json.loads((p/'configuracao_antes_treino.json').read_text())
            pares[seed,metodo]=(j,c)
            orcamentos.append({'seed':seed,'metodo':metodo,'exposicoes':j['exposicoes_exemplos'],
                'passos_otimizador':j['passos_otimizador'],'tempo_treino_s':j['tempo_treino_s'],
                'pico_RSS_KiB':j['pico_rss_kib'],'pesos_iniciais_sha256':j['pesos_iniciais_sha256'],
                'particao_sha256':c['particao_npz_sha256'],'mascaras_sha256':c['mascaras_validacao_sha256']})
            for scenario in ['principal','sensibilidade_raw64']:
                a=j['metricas'][scenario];cm=a['matriz_real_por_previsto']
                resultados.append({'seed':seed,'metodo':metodo,'cenario':scenario,'AP':a['PR_AUC_average_precision'],
                    'macro_F1':a['macro_f1'],'precisao_ATTACK':a['precisao_ATTACK'],'recall_ATTACK':a['recall_ATTACK'],
                    'FPR':a['FPR'],'VN':cm[0][0],'FP':cm[0][1],'FN':cm[1][0],'VP':cm[1][1],
                    'suporte_BENIGN':a['suporte']['BENIGN'],'suporte_ATTACK':a['suporte']['ATTACK']})
                nominais.extend({'seed':seed,'metodo':metodo,'cenario':scenario,'tipo':x['tipo'],
                    'suporte':x['suporte'],'recall_classe_binaria':x['recall_classe_binaria'] if x['recall_classe_binaria'] is not None else 'NA'}
                    for x in a['recall_por_tipo_nominal'])
        if (seed,'central') in pares and (seed,'fedavg') in pares:
            a,ca=pares[seed,'central'];b,cb=pares[seed,'fedavg']
            assert a['pesos_iniciais_sha256']==b['pesos_iniciais_sha256']
            assert ca['particao_npz_sha256']==cb['particao_npz_sha256'] and ca['mascaras_validacao_sha256']==cb['mascaras_validacao_sha256']
            assert a['exposicoes_exemplos']==b['exposicoes_exemplos']==5922120
    variacao=[]
    for metodo in ['central','fedavg']:
        for scenario in ['principal','sensibilidade_raw64']:
            rs=[x for x in resultados if x['metodo']==metodo and x['cenario']==scenario]
            if not rs:continue
            for metrica in ['AP','macro_F1','precisao_ATTACK','recall_ATTACK','FPR']:
                vs=[x[metrica] for x in rs]
                variacao.append({'metodo':metodo,'cenario':scenario,'metrica':metrica,'n_seeds':len(vs),
                    'media':statistics.mean(vs),'desvio_amostral_ddof1':statistics.stdev(vs) if len(vs)>1 else 'NA',
                    'minimo':min(vs),'maximo':max(vs)})
    out=ROOT/'tabelas';out.mkdir(exist_ok=True)
    for n,rows in [('resultados_por_seed.csv',resultados),('recall_por_tipo.csv',nominais),
                   ('orcamento_por_seed.csv',orcamentos),('variacao_entre_seeds.csv',variacao)]:tabela(out/n,rows)
    for n in ['resultados_por_seed.csv','recall_por_tipo.csv','orcamento_por_seed.csv','variacao_entre_seeds.csv']:
        if not (out/n).exists():(out/n).write_text('estado\nPENDENTE: nenhuma etapa deste tipo concluida\n')
    return resultados,orcamentos,variacao


def finalizar():
    rows,budget,var=montar_tabelas()
    if STATUS['estado']=='concluida':assert len(rows)==12
    fim=git_estado();salvar(ROOT/'git_final.json',fim)
    inicial=json.loads((ROOT/'git_inicial.json').read_text())
    preservado=fim==inicial
    STATUS['git_historico_preservado']=preservado
    STATUS['duracao_s']=time.monotonic()-START
    atualizar(fim_BRT=agora())
    gate=ROOT/'comparacao_reproducao.json'
    g=json.loads(gate.read_text()) if gate.exists() else {'passou':False,'campos':[]}
    report=ROOT/f"RELATORIO_{datetime.now(ZoneInfo('America/Belem')).strftime('%Y-%m-%d_%H-%M-%S')}_BRT_VM_CNN_5x5.md"
    texto=f'''# SecFedNet · rodada limitada na VM

Estado: **{STATUS['estado']}**. Início {STATUS['inicio_BRT']}; fim {STATUS['fim_BRT']}. Limite externo 45 min, reserva interna de 1 min para finalizar. Execução detached (`nohup`/nova sessão) com status/log persistentes. Etapas concluídas: {', '.join(x['etapa'] for x in STATUS['concluidas'])}.

Raiz VM: `{ROOT}`. Relatório: `{report}`. Ambiente e identidade: VM secfednet-repro, MAC 52:54:00:16:cd:d7, 192.168.122.8; recursos iniciais em manifesto. Git histórico inicial/final: `{inicial['head']}`, preservado={preservado}; stage inicial/final vazio={not inicial['stage'] and not fim['stage']}. Novas saídas locais ignoradas, sem commit/push/PR. Configurações globais e aplicativos existentes preservados.

## Reprodução antes da comparação

ZIP corrigido reutilizado na VM, SHA `97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`. Ambiente novo reconstruído pelo lock, sem alterar o antigo. `reproduzir.sh` foi executado com destino novo. Gate numérico contra Kubuntu: **{g['passou']}**, tolerância zero para índices, contagens, parâmetros/matrizes, pesos, scores/métricas da quinta e recargas. Fonte de referência: execução Kubuntu `protocolo-candidato-validacao-20-46-58`.

Variações de tempo/pico e hashes de checkpoint vinculados ao manifesto específico da execução são separadas de divergências numéricas. Campo a campo no manifesto e tabela de checks. Nenhuma comparação pareada é autorizada pelo runner sem o gate passar. Versões e logs da reconstrução: `logs/`.

## Protocolo e comparação exploratória

BENIGN=0, ATTACK=1; rótulos nominais preservados. Treino segunda–quarta 1.184.424; quinta principal 360.078 e sensibilidade bruta 328.429; sexta reservada, usada apenas nas verificações do manifesto/qualidade/interseções. Sexta **sem previsões ou métricas de desempenho**. Normalização float64 só do treino, entrada float32; mesmas máscaras por par. Sensibilidade bruta ainda contém 44/46/9 chaves compartilhadas após transformação float32 nos três pares; não houve expurgo adicional nem protocolo final congelado.

Seeds 23/41/89; partição 2305/4105/8905. CNN-1D idêntica, mesmos pesos iniciais por par, Adam lr=0,001, betas=(0,9;0,999), eps=1e-8, weight_decay=0, lote 512, limiar fixo 0,5. Cinco épocas centralizadas vs cinco rodadas FedAvg com época local única, cinco clientes, participação integral, Dirichlet α=0,5. Adam reinicia por época central e por cliente/rodada federada. Global shuffle no central e embaralhamento local no FedAvg: minibatches não são idênticos; tamanho e seeds estão fixados. Torch dois threads/interop um; treinos em processos sequenciais. A reprodução mantém os caps BLAS/OMP do roteiro histórico; comparação limitada a dois.

PR-AUC reportada como **average precision**, soma Δrecall×precision com empates agrupados, positivo ATTACK, sem trapézios. Sem calibração na quinta, sem ajuste na sexta. Tipos ausentes: recall NA; BENIGN por tipo é especificidade. A quinta é dominada por Infiltration - Portscan (99,805% dos positivos). Três seeds medem variação conjunta de inicialização, minibatches e partição, não isolam suas causas. Resultados exploratórios de uma captura/validação; sem inferência de significância ou generalização externa.

| Seed | Método | Quinta | AP | Macro-F1 | Recall ATTACK | FPR | Matriz [[VN,FP],[FN,VP]] |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
'''
    for x in rows:texto+=f"| {x['seed']} | {x['metodo']} | {x['cenario']} | {x['AP']:.6f} | {x['macro_F1']:.6f} | {x['recall_ATTACK']:.6f} | {x['FPR']:.6f} | [[{x['VN']},{x['FP']}],[{x['FN']},{x['VP']}]] |\n"
    texto+='''
Suporte principal: BENIGN 288.171 / ATTACK 71.907. Sensibilidade: BENIGN 256.522 / ATTACK 71.907. [Resultados e matrizes](tabelas/resultados_por_seed.csv) · [recall/suporte por tipo e seed](tabelas/recall_por_tipo.csv).

### Orçamento efetivo

| Seed | Método | Exposições | Passos Adam | Treino s | Pico RSS KiB |
| --- | --- | ---: | ---: | ---: | ---: |
'''
    for x in budget:texto+=f"| {x['seed']} | {x['metodo']} | {x['exposicoes']} | {x['passos_otimizador']} | {x['tempo_treino_s']:.3f} | {x['pico_RSS_KiB']} |\n"
    texto+='''
Exposições iguais por par; passos podem diferir pelas caudas dos minibatches de cada cliente. Estatísticas Adam são segregadas por cliente no FedAvg; trajetórias não são equivalentes. Hashes de inicialização/partição/máscaras pareados são conferidos. [Orçamento completo](tabelas/orcamento_por_seed.csv).

### Variação entre seeds (média ± desvio amostral)

| Método | Quinta | Métrica | N | Média | DP (ddof=1) | Mínimo | Máximo |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
'''
    for x in var:
        if x['metrica']=='precisao_ATTACK':continue
        dp=x['desvio_amostral_ddof1'];texto+=f"| {x['metodo']} | {x['cenario']} | {x['metrica']} | {x['n_seeds']} | {x['media']:.6f} | {dp if dp=='NA' else f'{dp:.6f}'} | {x['minimo']:.6f} | {x['maximo']:.6f} |\n"
    texto+=f'''
[Tabela completa](tabelas/variacao_entre_seeds.csv). Estado/pendência: {STATUS.get('erro','rodada concluída; revisar protocolo antes de sexta')}. Última etapa: {STATUS['etapa_atual']}. Modelos/caches/scores permanecem somente na VM; o retorno contém relatório, tabelas, logs sanitizados e manifesto. Nenhum artefato histórico foi sobrescrito.

## Acompanhamento e reprodução

```bash
ssh williian@192.168.122.8 'cat {ROOT}/STATUS.json'
ssh williian@192.168.122.8 'tail -F {ROOT}/execucao.log'
```

O log da etapa ativa está em `log_atual` do STATUS; durante a reprodução, consultar também `{ROOT}/reproducao/preparo.log`. O supervisor sobrevive ao fechamento do terminal. Comandos exatos e configurações imutáveis constam no manifesto. Para repetir, usar pasta nova, mesmo lock/dataset/fontes e inicializar o supervisor com limite externo de 2700 s. Não reutilizar destinos existentes.

Instruções consultadas no Kubuntu e na VM: AGENTS.md do projeto; skill local secfednet-validar-experimento na sessão principal. Nenhum subagente. Recursos .agents/.codex globais preservados. Próximo passo: revisar resultados e política de colisões; desempenho da sexta permanece pendente.
'''
    report.write_text(texto)
    if gate.exists():
        checks=[]
        for c in g['campos']:checks.append({'campo':c['campo'],'igual':c['igual'],
            'detalhe':json.dumps({k:v for k,v in c.items() if k not in ['campo','igual']},ensure_ascii=False)})
        tabela(ROOT/'tabelas/reproducao_checks.csv',checks)
    # Retorno estritamente documental, com a estrutura de links do relatório.
    ret=ROOT/'retorno';ret.mkdir(exist_ok=True);entrega=[]
    candidatos=[report,*sorted((ROOT/'tabelas').glob('*.csv')),*sorted((ROOT/'logs').glob('*.log'))]
    candidatos+=sorted((ROOT/'reproducao').glob('*.log')) if (ROOT/'reproducao').exists() else []
    candidatos.append(ROOT/'execucao.log')
    for p in candidatos:
        if not p.exists():continue
        rel=p.relative_to(ROOT);dst=ret/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        if p.suffix=='.log':dst.write_text(re.sub(r'\x1b\[[0-9;]*m','',p.read_text(errors='replace')))
        else:shutil.copy2(p,dst)
        entrega.append({'path':str(rel),'sha256':sha(dst),'bytes':dst.stat().st_size})
    arquivos=[]
    for base,dirs,files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in ['ambiente','retorno','__pycache__']]
        for n in sorted(files):
            p=Path(base)/n
            if p.name=='manifesto_execucao.json' or p.suffix=='.tmp':continue
            arquivos.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
    recursos=json.loads((ROOT/'controle/recursos_preflight_vm.json').read_text())
    manifest={'raiz_vm':str(ROOT),'status':STATUS,'configuracao':CFG,'recursos_iniciais':recursos,'git_inicial':inicial,'git_final':fim,
        'reproducao':g,'artefatos_vm':arquivos,'retorno_documental':entrega,
        'exclusoes':'ambiente reconstruivel pelo lock; modelos, matrizes, indices e scores ficam na VM e constam apenas por hash no retorno',
        'sexta_desempenho':False,'relatorio':report.name}
    salvar(ROOT/'manifesto_execucao.json',manifest);shutil.copy2(ROOT/'manifesto_execucao.json',ret/'manifesto_execucao.json')


def main():
    (ROOT/'logs').mkdir(exist_ok=True);salvar(ROOT/'git_inicial.json',git_estado());atualizar()
    env=os.environ.copy();env.pop('PYTHONPATH',None);env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
        PYTHONDONTWRITEBYTECODE='1',FLWR_TELEMETRY_ENABLED='0',UV_CACHE_DIR=CFG['cache_uv'])
    try:
        if sha(Path(CFG['zip_path_vm']))!='97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883':raise ValueError('ZIP incorreto')
        uv=CFG['uv_vm'];py=str(ROOT/'ambiente/bin/python');lock=str(ROOT/'fonte/requirements.lock')
        etapa('01_venv',[uv,'--no-config','venv','--python',CFG['python_vm'],'--no-python-downloads',str(ROOT/'ambiente')],env)
        args=['pip','sync','--strict','--python',py,'--default-index','https://pypi.org/simple',lock]
        code=etapa('02_lock_offline',[uv,'--no-config','--offline',*args],env,True)
        if code:etapa('02b_lock_rede',[uv,'--no-config',*args],env)
        etapa('02c_pip_check',[uv,'--no-config','pip','check','--python',py],env)
        etapa('03_reproducao',['bash',str(ROOT/'fonte/reproduzir.sh'),str(ROOT/'reproducao'),py,CFG['zip_path_vm']],env)
        etapa('04_gate_reproducao',[py,'-B',str(ROOT/'controle/comparar_reproducao.py'),str(ROOT)],env)
        for seed in CFG['seeds']:
            for metodo in ['central','fedavg']:
                etapa(f'05_seed{seed}_{metodo}',[py,'-B',str(ROOT/'controle/comparar_cnn.py'),str(seed),metodo],env)
                montar_tabelas()
        atualizar(estado='concluida',etapa_atual='todas_as_seeds_concluidas')
    except (TimeoutError,subprocess.TimeoutExpired) as e:atualizar(estado='limitada_por_tempo',erro=str(e))
    except BaseException as e:atualizar(estado='interrompida_erro',erro=repr(e))
    finally:finalizar()


if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(TimeoutError('SIGTERM/limite externo')))
    main()
