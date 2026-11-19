"""Bounded Pro compilation, one source evaluation at a time, no native fallback."""
import argparse,io,json,math,sys,time
from pathlib import Path
from contextlib import redirect_stdout
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'FlowEvo/src'),'/private/tmp/flowevo_route_d1_tokenizers']
import run_alfworld_route_c_bounded_learning as C
import run_alfworld_revision_feedback as R
from alfworld_revision_environment import SelectedTrainEnv
from alfworld_revision_delivery import extract_candidate
from alfworld_absolute_deadline import absolute_deadline,capturing_factory
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.evidence import EvidenceStore
from failure_evo.model_api import configured_api_key
from failure_evo.network_transport import post_deepseek
from failure_evo.run_health import trusted_usage
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from tokenizers import Tokenizer
A=C.A
TOKENIZER=ROOT.parent/'experiments/reasoning_token_attribution_and_replacement/tokenizer/tokenizer.json'
SYSTEM=C.SOURCE_CONTRACT+'''
Return one JSON object with complete code, description and applicability strings.
Keep descriptions brief. Put complete Python in the FINAL content, not reasoning.
Source <=65536 UTF-8 bytes. No classes, async, global or nonlocal declarations.
No dynamic execution, reflection, filesystem, networking, dunder access or model
calls. Only ordinary functions, allowlisted imports and module literal constants.
Runtime receives exactly goal, observation, admissible_commands, history, state.
History has action/observation pairs only. State starts empty and is carried forward.
State <=4096 UTF-8 bytes; entire return <=8192. Worker call timeout 2 seconds,
256 MiB memory, one CPU, no network. Return applied with a current legal action,
or declined with reason; there is no success return. Only environment won proves
completion. No native model completes the task after the skill exits.
Compile from the one real failed episode and first actual successful recovery.
Main objective: from the original step-16 state complete the task within remaining
34 actions. Partial progress is not a passing result. Learn parameterized logic:
bind target type/instances, destination type/instances, location, held object,
state changes and next action from each runtime's public information. Do not
hardcode source instance numbers, answer locations, a fixed action sequence or a
source search-location list. Goal containing keychain cannot be the sole scope
condition. Host will not calculate missing inventory, location or progress for you.
Do not reconstruct Python from old reasoning or use other models' programs.
If feedback is present, it belongs to the named executed version. Preserve and
revise the supplied full source; use only actual feedback, no imagined observations.
'''

def meter(wire):
    t=Tokenizer.from_file(str(TOKENIZER));n=sum(len(t.encode(m['content'],add_special_tokens=False).ids) for m in wire['messages'])
    return dict(local_content_tokens=n,margin_formula='ceil(local_content_tokens * 1.25) + 1024',estimated_input_upper=math.ceil(n*1.25)+1024,input_token_limit=65536,wire_bytes=len(C.canonical(wire).encode()),tokenizer_sha256=A.sha(TOKENIZER),method='local DeepSeek tokenizer surrogate, calibrated offline against 41 Route D provider usage records; not exact current server tokenizer')

def cases():return A.read(OLD/'development.private.json')
OLD=ROOT/'runs/alfworld_route_d_20261118_01'

def frozen(root):
    p=A.read(root/'protocol.json')
    for path,h in p['dependencies'].items():
        if A.sha(Path(path))!=h:raise RuntimeError('FROZEN_DEPENDENCY_CHANGED')
    return p

class Env:
    def __init__(self,base,study):self.base=base;self.study=study;self.phase='prefix'
    def step(self,action):
        s=self.study;s.health();rows=s.env_events.records();n=sum(x['kind']=='STARTED' for x in rows)+1
        if n>600:raise RuntimeError('ENVIRONMENT_LIMIT')
        p=dict(number=n,branch=s.ident,phase=self.phase,action=action);s.env_events.append('STARTED',p,time.time())
        try:r=self.base.step(action)
        except BaseException as e:s.env_events.append('ERROR',dict(p,error=type(e).__name__),time.time());raise
        s.env_events.append('RETURNED',dict(p,feedback=C.feedback(action,r)),time.time());return r
    def close(self):self.base.close()

class Study(C.Study):
    def __init__(self,root):
        self.root=root;self.p=frozen(root);self.ident=''
        self.budget=PersistentBudget(root/'budget.jsonl',run_id=root.name,protocol_hash=A.digest(self.p),max_calls=4,max_tokens=4*(65536+32768),max_tools=400,max_cost_microusd=2000000,token_rate_microusd_per_million=3960000,tool_cost_upper_microusd=0,max_tool_milliseconds=4000000,tool_milliseconds_upper=10000,wall_seconds=5400)
        self.events=EvidenceStore(root/'events.jsonl');self.env_events=EvidenceStore(root/'environment_actions.jsonl')
        es=self.env_events.records()
        if {x['payload']['number'] for x in es if x['kind']=='STARTED'}!={x['payload']['number'] for x in es if x['kind']=='RETURNED'}:raise RuntimeError('UNKNOWN_ENVIRONMENT_STATE')
        self.backend=FrozenLinuxBackend(image=self.p['worker']['image'],worker_script=self.p['worker']['worker_script'])
        assert self.backend.manifest()==self.p['worker']
    def health(self):
        if self.budget.remaining_seconds<=0:raise RuntimeError('TOTAL_WALL_LIMIT')
        if self.budget.blocking_requests(self.p['network_policy']):raise RuntimeError('REQUEST_STATUS_UNKNOWN')
    def request(self,ident,wire):
        self.health();folder=self.root/'requests'/ident
        if folder.exists():raise RuntimeError('NO_REQUEST_REISSUE')
        measurement=meter(wire);A.commit(folder/'input_measurement.json',measurement)
        if measurement['estimated_input_upper']>65536:raise RuntimeError('INPUT_TOKEN_LIMIT_NO_TRUNCATION')
        A.commit(folder/'request.private.json',wire)
        # Reserve the full permitted input count, not the surrogate estimate.
        # Uniform peak output rate is stricter than split peak input/output pricing.
        self.budget.reserve_network(65536,wire['max_tokens'],job_id=ident,capability='model',request_id=ident,request_hash=A.digest(wire),policy=self.p['network_policy'],wire_hash=A.digest(wire))
        start=time.time();A.commit(folder/'start.json',dict(wall_start=start,absolute_deadline_seconds=min(600,self.budget.remaining_seconds),socket_wait_seconds=120))
        try:
            with absolute_deadline(min(600,self.budget.remaining_seconds)):
                raw=post_deepseek(wire,configured_api_key(),budget=self.budget,request_id=ident,policy=self.p['network_policy'],connection_factory=capturing_factory(folder),emit=lambda k,p:self.events.append(k,p,time.time()))
        finally:A.commit(folder/'end.json',dict(wall_end=time.time(),elapsed_seconds=time.time()-start))
        A.commit(folder/'response.json',raw);usage=trusted_usage(raw)
        if not usage:self.budget.settle(ident);raise RuntimeError('REQUEST_STATUS_UNKNOWN')
        self.budget.settle(ident,tokens=usage['total_tokens'])
        if usage['input_tokens']>65536:raise RuntimeError('ACTUAL_INPUT_TOKEN_LIMIT')
        if raw.get('model')!='deepseek-v4-pro':raise RuntimeError('PROVIDER_MODEL_MISMATCH')
        if usage['input_tokens']>measurement['estimated_input_upper']:raise RuntimeError('INPUT_ESTIMATOR_MARGIN_EXCEEDED')
        return raw
    def reset(self,case):
        self.health();t=case['task'];game=Path(self.p['data_root'])/t['game']
        if A.sha(game)!=t['game_sha256'] or A.sha(game.with_name('traj_data.json'))!=t['trajectory_sha256']:raise RuntimeError('SOURCE_CHANGED')
        base=SelectedTrainEnv(self.p['data_root'],50);env=Env(base,self)
        try:
            with redirect_stdout(io.StringIO()):base.initialize(frozen_game_files=[str(game)]);task,obs,cmds=base.reset()
            assert task.goal==case['goal'] and obs==case['initial']['observation'] and list(cmds)==case['initial']['commands']
            for step in case['steps']:
                assert step['action'] in cmds
                rr=env.step(step['action']);actual=C.feedback(step['action'],rr)
                assert actual=={k:step[k] for k in actual},'PREFIX_MISMATCH'
                obs,cmds=rr.observation,list(rr.admissible_commands)
            env.phase='suffix';return env,obs,cmds
        except BaseException:env.close();raise
    def worker(self,code,context,path):
        self.health();result=super().worker(code,context,path)
        if A.read(path)['raw'].get('status') in ('WORKER_ERROR','EVALUATOR_ERROR'):raise RuntimeError('WORKER_INFRASTRUCTURE_ERROR')
        return result

def submissions(root):return [A.read(p) for p in sorted((root/'candidates').glob('v*/submission.json'))]

def generate(root,kind):
    study=Study(root);subs=submissions(root);slots=[A.read(x) for x in sorted((root/'slots').glob('*.json'))]
    if (root/'Selected.json').exists():raise RuntimeError('SOURCE_ALREADY_PASSED')
    if kind=='draft' and slots:raise RuntimeError('DRAFT_ALREADY_USED')
    if kind=='revision' and (not subs or sum(x['kind']=='revision' for x in slots)>=2):raise RuntimeError('REVISION_LIMIT')
    if len(slots)>=4:raise RuntimeError('REQUEST_LIMIT')
    fallback_used=any(x['kind']=='fallback' for x in slots)
    if kind=='fallback':
        if fallback_used or not subs or subs[-1]['extraction']['passed']:raise RuntimeError('FALLBACK_NOT_ALLOWED')
        previous=A.read(root/'requests'/slots[-1]['version']/'request.private.json');messages=previous['messages'];fallback=True
    else:
        if subs and not subs[-1]['extraction']['passed']:raise RuntimeError('UNDELIVERED_SOURCE_REQUIRES_SINGLE_FALLBACK_OR_STOP')
        evaluations=[A.read(p) for p in sorted((root/'evaluations').glob('v*/source.json'))]
        latest=subs[-1] if subs else None;source=next((s for s in reversed(subs) if s['code_path']),None)
        feedback=None
        if latest:
            feedback=dict(latest_submission_version=latest['version'],static=latest['static'],delivery_errors=latest['extraction']['errors'],parameterization=A.read(root/'candidates'/latest['version']/'parameterization.json') if (root/'candidates'/latest['version']/'parameterization.json').exists() else None,executed=evaluations[-1] if evaluations else None)
        payload=dict(instruction='Return a JSON object containing complete Python code, description and applicability. No verbose explanation.',material=A.read(root/'learning_material.json'),source_to_revise=dict(version=source['version'],sha256=source['code_sha256'],code=Path(source['code_path']).read_text()) if source else None,feedback=feedback)
        messages=[dict(role='system',content=SYSTEM),dict(role='user',content=C.canonical(payload))];fallback=fallback_used
    wire=dict(model='deepseek-v4-pro',messages=messages,thinking={'type':'disabled' if fallback else 'enabled'},reasoning_effort='none' if fallback else 'low',max_tokens=16384 if fallback else 32768,response_format={'type':'json_object'},stream=False)
    if fallback:wire['temperature']=0
    version=f'v{len(slots)+1}';A.commit(root/'slots'/f'{version}.json',dict(kind=kind,version=version,fallback=fallback))
    raw=study.request(version,wire)
    # Finish length is a delivery failure even if a partial string looks like code.
    sub=R.submitted(root,version,raw,dict(kind=kind,configuration='fallback' if fallback else 'low'))
    content=raw['choices'][0]['message'].get('content') or ''
    A.commit(root/'requests'/version/'Delivery_Metrics.json',dict(finish_reason=raw['choices'][0]['finish_reason'],content_chars=len(content),source_chars=len(sub['extraction']['code']) if sub['extraction']['code'] else 0,source_bytes=len(sub['extraction']['code'].encode()) if sub['extraction']['code'] else 0,usage=raw['usage'],response_model=raw.get('model'),response_id=raw.get('id'),complete_source=sub['extraction']['passed']))
    print(json.dumps(dict(version=version,delivery=sub['extraction']['passed'],static=sub['static'],code_path=sub['code_path']),ensure_ascii=False),flush=True)

def evaluate(root,version,diagnostics=False):
    study=Study(root);sub=A.read(root/'candidates'/version/'submission.json');review=A.read(root/'candidates'/version/'parameterization.json')
    if not sub['static']['passed'] or not review['passed']:raise RuntimeError('CANDIDATE_NOT_ADMITTED')
    selected=root/'Selected.json'
    indices=[1,2,3] if diagnostics else [0]
    if diagnostics and (not selected.exists() or A.read(selected)['version']!=version):raise RuntimeError('DIAGNOSTIC_REQUIRES_FROZEN_SOURCE_PASS')
    old=None
    if not diagnostics:
        for p in (root/'evaluations').glob('*/source.json'):
            ev=A.read(p)
            if ev['code_sha256']==sub['code_sha256']:old=ev;break
    for j in indices:
        case=A.read(root/'development.private.json')[j];folder=root/'evaluations'/version/f'development_{j}';study.ident=str(folder.relative_to(root))
        if old is not None:
            row=dict(old,reused_from=old['version'],version=version)
        else:
            if (folder/'result.json').exists() or (folder/'exclusion_worker.json').exists():raise RuntimeError('NO_DUPLICATE_EVALUATION')
            if j<3:study.branch(case,study.ident,'F',Path(sub['code_path']),development=True)
            else:
                env,obs,cmds=study.reset(case)
                try:study.worker(Path(sub['code_path']),C.context_view(case['goal'],obs,cmds,C.history(case['steps']),{}),folder/'exclusion_worker.json')
                finally:env.close()
            evidence=R.branch_evidence(case,folder,version,sub['code_sha256'],boundary=j==3)
            row=dict(version=version,code_sha256=sub['code_sha256'],reused_from=None,**evidence)
        A.commit(root/'evaluations'/version/('source.json' if j==0 else f'diagnostic_{j}.json'),row)
        print(json.dumps(row['summary'],ensure_ascii=False),flush=True)
        if j==0 and row['summary']['environment_won']:
            A.commit(selected,dict(version=version,code_sha256=sub['code_sha256'],parameterization_review_sha256=A.sha(root/'candidates'/version/'parameterization.json'),selected_before_diagnostics=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('command',choices=['draft','revision','fallback','evaluate','diagnostics']);p.add_argument('--version');args=p.parse_args()
    try:
        if args.command in ('draft','revision','fallback'):generate(args.root,args.command)
        else:evaluate(args.root,args.version,args.command=='diagnostics')
    except BaseException as exc:
        A.commit(args.root/f'Stopped_{args.command}_{int(time.time())}.json',dict(error_type=type(exc).__name__,message=str(exc),at=C.stamp()));raise
