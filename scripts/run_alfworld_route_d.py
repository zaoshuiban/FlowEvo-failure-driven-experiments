"""Authorized Route D orchestration using existing ALFWorld/Worker/transport."""
import argparse,copy,http.client,io,json,ssl,sys,time
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
import run_alfworld_route_c_bounded_learning as C
import run_alfworld_revision_feedback as R
from alfworld_route_d_interface import public_state,wire_for,discover,canonical
from alfworld_revision_environment import SelectedTrainEnv
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.evidence import EvidenceStore
from failure_evo.model_api import configured_api_key
from failure_evo.network_transport import post_deepseek
from failure_evo.run_health import trusted_usage
from failure_evo.autonomous_mvp import FrozenLinuxBackend
A=C.A
OUT=ROOT/'runs/alfworld_route_d_20261118_01'
REPORT=ROOT/'reports/alfworld_route_d_20261118_01'
MODELS=['deepseek-flash','deepseek-v4-pro']

def save(p,v):return A.commit(p,v)

def verify():
    p=A.read(OUT/'Preparation_Manifest.json');f=A.read(OUT/'P0_Completion.json')
    assert A.sha(REPORT/'Route_D_Protocol.md')==f['protocol_sha256']
    assert A.sha(OUT/'Budget_Proposal.json')==f['budget_sha256']
    for path,h in p['dependencies'].items():assert A.sha(Path(path))==h
    auth=A.read(OUT/'Authorization.json')
    assert auth['protocol_sha256']==f['protocol_sha256'] and auth['max_usd']==34 and auth['authorized'] is True
    return p

class Env:
    def __init__(self,base,study):self.base=base;self.study=study;self.phase='prefix'
    def step(self,action):
        s=self.study;s.health()
        rows=s.env_events.records();starts=[x for x in rows if x['kind']=='STARTED']
        phase='P1' if s.ident.startswith('P1/') else 'P3'
        if len(starts)>=1400 or sum(x['payload']['stage']==phase for x in starts)>=(200 if phase=='P1' else 1200):raise RuntimeError('ENV_LIMIT')
        n=len(starts)+1;p=dict(number=n,branch=s.ident,stage=phase,phase=self.phase,action=action)
        s.env_events.append('STARTED',p,time.time())
        try:r=self.base.step(action)
        except BaseException as e:
            s.env_events.append('ERROR',dict(p,error=type(e).__name__),time.time());raise
        s.env_events.append('RETURNED',dict(p,feedback=C.feedback(action,r)),time.time());return r
    def close(self):self.base.close()

class Study(C.Study):
    def __init__(self,model):
        self.root=OUT;self.model_id=model;m=verify();self.p=m['old_protocol'];self.p['model']=model
        f=A.read(OUT/'P0_Completion.json');self.p['network_policy']=m['old_protocol']['network_policy'];self.ident=''
        s=model==MODELS[1]
        start=OUT/'Execution_Start.json'
        if not start.exists():save(start,dict(started=time.time(),deadline=time.time()+21600))
        self.deadline=A.read(start)['deadline']
        self.budget=PersistentBudget(OUT/f'budget_{model}.jsonl',run_id=OUT.name+'/'+model,protocol_hash=f['protocol_sha256'],max_calls=79,
            max_tokens=6459136 if s else 5889792,max_tools=300,max_cost_microusd=26800000 if s else 7200000,
            token_rate_microusd_per_million=3960000 if s else 1200000,tool_cost_upper_microusd=0,
            max_tool_milliseconds=3000000,tool_milliseconds_upper=10000,wall_seconds=21600)
        self.events=EvidenceStore(OUT/'events.jsonl');self.env_events=EvidenceStore(OUT/'environment_actions.jsonl')
        rows=self.env_events.records();beg={x['payload']['number'] for x in rows if x['kind']=='STARTED'};end={x['payload']['number'] for x in rows if x['kind']=='RETURNED'}
        if beg!=end:raise RuntimeError('ENVIRONMENT_UNKNOWN_OR_ERROR')
        self.backend=FrozenLinuxBackend(image=self.p['worker']['image'],worker_script=self.p['worker']['worker_script'])
        assert self.backend.manifest()==self.p['worker']
    def health(self):
        if time.time()>=self.deadline:raise RuntimeError('WALL_LIMIT')
        if self.budget.blocking_requests(self.p['network_policy']):raise RuntimeError('UNKNOWN_OR_PENDING_REQUEST')
    def request(self,ident,wire,cap):
        self.health();folder=OUT/'requests'/ident
        if (folder/'response.json').exists():return A.read(folder/'response.json')
        size=len(canonical(wire).encode());save(folder/'Input_Size.json',dict(bytes=size,limit=cap,passed=size<=cap))
        if size>cap:raise RuntimeError('INPUT_LIMIT_NO_TRUNCATION')
        save(folder/'request.private.json',wire)
        save(OUT/'logical_slots'/(ident+'.json'),dict(ident=ident,model=self.model_id,wire_sha256=A.digest(wire)))
        count=len(list((OUT/'logical_slots'/ident.split('/')[0]/self.model_id).rglob('*.json')))
        if count>(76 if ident.startswith('P1/') else 3):raise RuntimeError('PHASE_REQUEST_LIMIT')
        self.budget.reserve_network(size+256,wire['max_tokens'],job_id=ident,capability='model',request_id=ident,request_hash=A.digest(wire),policy=self.p['network_policy'],wire_hash=A.digest(wire))
        raw=post_deepseek(wire,configured_api_key(),budget=self.budget,request_id=ident,policy=self.p['network_policy'],emit=lambda k,p:self.events.append(k,p,time.time()))
        save(folder/'response.json',raw);usage=trusted_usage(raw)
        if not usage:
            self.budget.settle(ident);raise RuntimeError('PROVIDER_ERROR_OR_UNKNOWN_USAGE')
        self.budget.settle(ident,tokens=usage['total_tokens'])
        if raw.get('model')!=self.model_id:raise RuntimeError('MODEL_IDENTITY_MISMATCH')
        print(json.dumps(dict(request=ident,usage=usage)),flush=True)
        return raw
    def reset(self,case):
        self.health();game=Path(self.p['data_root'])/case['task']['game']
        assert A.sha(game)==case['task']['game_sha256'] and A.sha(game.with_name('traj_data.json'))==case['task']['trajectory_sha256']
        base=SelectedTrainEnv(self.p['data_root'],50);env=Env(base,self)
        try:
            with redirect_stdout(io.StringIO()):base.initialize(frozen_game_files=[str(game)]);task,obs,cmds=base.reset()
            assert task.goal==case['goal'] and obs==case['initial']['observation'] and list(cmds)==case['initial']['commands']
            for step in case['steps']:
                assert step['action'] in cmds
                r=env.step(step['action']);actual=C.feedback(step['action'],r)
                assert actual=={k:step[k] for k in actual},'PREFIX_MISMATCH'
                obs,cmds=r.observation,list(r.admissible_commands)
            env.phase='suffix';return env,obs,cmds
        except BaseException:env.close();raise
    def worker(self,code,context,path):
        self.health();result=super().worker(code,context,path)
        if A.read(path)['raw'].get('status') in ('WORKER_ERROR','EVALUATOR_ERROR'):raise RuntimeError('WORKER_INFRASTRUCTURE_ERROR')
        return result

def availability():
    verify();p=OUT/'Model_Availability.json'
    if p.exists():return A.read(p)
    key=configured_api_key();conn=http.client.HTTPSConnection('api.deepseek.com',timeout=30,context=ssl.create_default_context())
    try:
        conn.request('GET','/models',headers={'Authorization':'Bearer '+key})
        response=conn.getresponse();text=response.read(1024*1024).decode().replace(key,'[REDACTED]')
        value=dict(status=response.status,body=json.loads(text),at=C.stamp(),inference_calls=0)
        save(p,value)
        if response.status!=200:raise RuntimeError('MODEL_LIST_UNAVAILABLE')
        return value
    finally:conn.close()

def p1():
    avail=availability();ids={x['id'] for x in avail['body']['data']};case=A.read(OUT/'checkpoint.private.json');results=[]
    for model in MODELS:
        if model not in ids:
            save(OUT/f'{model}_unavailable.json',dict(status='MODEL_UNAVAILABLE'));continue
        study=Study(model)
        for attempt in (1,2):
            ident=f'P1/{model}/attempt_{attempt}';folder=OUT/ident
            if (folder/'result.json').exists():results.append(A.read(folder/'result.json'));continue
            if folder.exists() and list(folder.glob('request*')):raise RuntimeError('PARTIAL_ATTEMPT_NO_AUTOMATIC_RESTART')
            study.ident=ident;env,_,_=study.reset(case)
            try:
                result=discover(case,env,lambda state,n:study.request(ident+f'/r{n:02d}',wire_for(state,model),65536),lambda k,v:save(folder/(k+'.json'),v),C.feedback)
            finally:env.close()
            result.update(model_id=model,run_id=OUT.name,attempt=attempt,source_checkpoint_sha256=A.sha(OUT/'checkpoint.private.json'),initial_public_context_hash=A.read(OUT/'Preparation_Manifest.json')['initial_public_context_sha256'])
            save(folder/'result.json',result);results.append(result)
            print(json.dumps(dict(attempt=ident,won=result['won'],actions=result['environment_actions'])),flush=True)
    selected=next((dict(model=x['model_id'],attempt=x['attempt']) for x in results if x['won']),None)
    save(OUT/'P1_Result.json',dict(results=results,selected=selected,status='RECOVERY_DISCOVERED' if selected else 'RECOVERY_DISCOVERY_NOT_ESTABLISHED'))

COMPILE_PROMPT=C.SOURCE_CONTRACT+'''
Compile a reusable recovery policy from the real original failure and the selected
actual successful model recovery. Historical instance numbers belong only to that
episode. Bind objects and containers using each future episode's public evidence.
Do not replay a fixed action list or hardcode instance IDs. Do not choose the first
legal command as a generic fallback. Support two-object recovery and decline when
inapplicable or evidence is insufficient. Do not sum placements across different
containers into a completion claim. Do not categorically forbid all retrieval.
Attempt the whole task within its original remaining budget. Only environment won
establishes episode completion. Partial progress must not claim episode success.
No native model will finish after you decline. State starts empty. Keep state <=4096
UTF-8 bytes and return <=8192 bytes. An inert outer metadata field does not invalidate
unique source. All algorithmic choices are yours. Feedback, when present, belongs
only to the explicitly named executed version. Revise the complete source supplied.
'''

def p2():
    discovery=A.read(OUT/'P1_Result.json');sel=discovery['selected']
    if not sel:save(OUT/'P2_Result.json',dict(status='NOT_RUN_NO_SUCCESSFUL_RECOVERY'));return
    recovery=A.read(OUT/f"P1/{sel['model']}/attempt_{sel['attempt']}/result.json")
    failure=A.read(ROOT/'runs/alfworld_skill_revision_feedback_20261118_01/learning_input.json')['episodes'][0]
    common=dict(original_failure=failure,selected_recovery=dict(goal=failure['goal'],prefix=C.history(A.read(OUT/'checkpoint.private.json')['steps']),recovery_steps=recovery['steps'],won=True,origin=sel))
    save(OUT/'Compilation_Material.json',common);cases=A.read(OUT/'development.private.json');all_chains=[]
    ids={x['id'] for x in A.read(OUT/'Model_Availability.json')['body']['data']}
    for model in MODELS:
        if model not in ids:continue
        study=Study(model);latest=None;source=None;executed=None;chain=[]
        for iteration in range(1,4):
            version=model+f'_v{iteration}';payload=dict(material=common,latest_submission=latest,source_to_revise=source,last_execution=executed)
            wire=wire_for({},model);wire['messages']=[dict(role='system',content=COMPILE_PROMPT),dict(role='user',content=canonical(payload))];wire['max_tokens']=16384 if model==MODELS[1] else 8192
            raw=study.request(f'P2/{model}/r{iteration}',wire,262144)
            sub=R.submitted(OUT,version,raw,dict(model=model,iteration=iteration,selected_recovery=sel));latest=dict(version=version,code_sha256=sub['code_sha256'],errors=sub['extraction']['errors'],static=sub['static'])
            if sub['code_path']:source=dict(version=version,sha256=sub['code_sha256'],code=Path(sub['code_path']).read_text())
            rows=[]
            if sub['static']['passed']:
                for j,case in enumerate(cases):
                    ident=f'P3/{version}/development_{j}';folder=OUT/ident;study.ident=ident
                    if j<3:study.branch(case,ident,'F',Path(sub['code_path']),development=True)
                    else:
                        env,obs,cmds=study.reset(case)
                        try:study.worker(Path(sub['code_path']),C.context_view(case['goal'],obs,cmds,C.history(case['steps']),{}),folder/'exclusion_worker.json')
                        finally:env.close()
                    rows.append(R.branch_evidence(case,folder,version,sub['code_sha256'],boundary=j==3))
                executed=dict(version=version,code_sha256=sub['code_sha256'],branches=rows)
                # Latest execution only; no growing archive and no host diagnosis.
            passed=bool(rows and rows[0]['summary']['environment_won'] and rows[3]['summary']['declined_without_action'] and not any(x['summary']['runtime_errors'] or x['summary']['false_completion_claim'] for x in rows)
                and all(x['summary']['environment_won'] or x['summary']['declined_without_action'] for x in rows[1:3]))
            result=dict(version=version,model=model,static=sub['static'],branches=rows,passed=passed)
            save(OUT/'evaluations'/version/'evaluation.json',result);chain.append(result)
            print(json.dumps(dict(version=version,passed=passed,wins=[x['summary']['environment_won'] for x in rows])),flush=True)
            if passed:break
        all_chains.append(dict(model=model,versions=chain,selected=next((x['version'] for x in chain if x['passed']),None)))
    selected=next((x['selected'] for x in all_chains if x['selected']),None)
    save(OUT/'P2_Result.json',dict(chains=all_chains,selected=selected,P4='NOT_AUTHORIZED_NOT_RUN'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['availability','P1','P2']);args=parser.parse_args()
    try: {'availability':availability,'P1':p1,'P2':p2}[args.phase]()
    except BaseException as e:
        save(OUT/f'Stopped_{args.phase}_{int(time.time())}.json',dict(error_type=type(e).__name__,message=str(e),at=C.stamp()))
        raise
