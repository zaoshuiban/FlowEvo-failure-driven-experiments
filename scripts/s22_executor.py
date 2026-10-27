"""Frozen S22 executor. No retries; explicit new authorization required for network.

An interrupted, unfinished branch stops on restart, even if raw output exists.
Manual reconciliation never implicitly permits resending. Mock state cannot be
promoted to real state. Sealed evaluation is a separate, offline command.
"""
import argparse,fcntl,hashlib,json,os,pathlib,sys,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint
from failure_evo.workflow_protocol_v2 import prepare,SharedTransport,delivery
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.runtime import Budget
from s22_action_audit import compare,profile
BASE=ROOT/'reports/s22_action_preference_v1'
MANIFEST=ROOT/'reports/s22_executor_v1/manifest.json'
def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,obj):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',dir=p.parent,delete=False) as f:
        f.write(canonical(obj)+'\n');f.flush();os.fsync(f.fileno());name=f.name
    os.replace(name,p)
    fd=os.open(p.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def verify():
    p=read(BASE/'protocol.json');assert fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})==p['protocol_hash']
    for section in ('sources','artifacts'):
        for path,h in p[section].items():
            if sha(ROOT/path)!=h:raise ValueError('FROZEN_HASH_MISMATCH: '+path)
    m=read(MANIFEST)
    if m['base_protocol_hash']!=p['protocol_hash']:raise ValueError('base binding')
    for path,h in m['sources'].items():
        if sha(ROOT/path)!=h:raise ValueError('executor binding: '+path)
    return p,m

def authorize(auth,run_id,p,m):
    expected=dict(run_id=run_id,protocol_hash=p['protocol_hash'],executor_hash=fingerprint(m),api_spend_authorized=True,max_cost_microusd=1000000,max_calls=20)
    if auth!=expected:raise PermissionError('New explicit run/protocol/executor-bound $1 authorization required')

class ScopedBudget(PersistentBudget):
    task_scope=None
    def tool(self,**kwargs):
        if self.task_scope is not None:self.task_scope.tool()
        return super().tool(**kwargs)

def ledger(path,run_id,binding):
    return ScopedBudget(path,run_id=run_id,protocol_hash=binding,max_calls=20,max_tokens=819200,max_tools=1000,max_cost_microusd=1000000,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=12000000,tool_milliseconds_upper=20000,wall_seconds=21600)

def worker(budget,directory):
    import run_workflow_v2 as e
    cfg=read(BASE/'worker_acceptance.json')['worker_manifest']['worker_environment']
    os.environ.update(DOCKER_HOST=cfg['docker_host'],DOCKER_CONFIG=cfg['docker_config'])
    tmp=directory/'tmp';tmp.mkdir(exist_ok=True);tempfile.tempdir=str(tmp)
    return e.prior.Judge(budget).run

def mock_sender(wire,timeout):
    return dict(model=json.loads(wire)['model'],usage=dict(prompt_tokens=100,completion_tokens=10,total_tokens=110),choices=[dict(finish_reason='stop',message=dict(content='```python\nprint(0)\n```'))])
def mock_judge(tid,code,cases):return dict(passed=False,status='WRONG_ANSWER',tests_run=len(cases),tests_passed=0,seconds=0,mock=True)
def real_sender(wire,timeout):
    from failure_evo.model_api import DeepSeekGenerator,configured_api_key
    return DeepSeekGenerator._post(json.loads(wire),configured_api_key(),timeout)

def run(directory,*,mode='mock',auth=None,sender=None,judge=None):
    p,m=verify();directory=pathlib.Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
    if mode not in ('mock','real'):raise ValueError('mode')
    if mode=='real':authorize(auth,directory.name,p,m)
    with (directory/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        binding=fingerprint(m)
        identity=dict(run_id=directory.name,mode=mode,protocol_hash=p['protocol_hash'],executor_hash=binding)
        ip=directory/'identity.json'
        if ip.exists() and read(ip)!=identity:raise ValueError('RUN_IDENTITY_CHANGED')
        save(ip,identity)
        budget=ledger(directory/'budget.jsonl',directory.name,binding)
        sp=directory/'state.json'
        state=read(sp) if sp.exists() else dict(status='READY',branches={})
        if state['status']=='ONLINE_LOCKED':return state
        if state['status'].startswith('STOPPED'):raise RuntimeError('STOPPED_RUN_NO_AUTOMATIC_RESUME')
        if budget.snapshot()['unknown_or_pending_requests'] or any(v['request_state']!='COMPLETED' for v in state['branches'].values()):
            state['status']='STOPPED_UNRECONCILED';save(sp,state);raise RuntimeError(state['status'])
        send=sender or (mock_sender if mode=='mock' else real_sender)
        evaluate=judge or (mock_judge if mode=='mock' else worker(budget,directory))
        try:
            for i,arms in enumerate(p['arm_order'],1):
                frozen=read(BASE/f'frozen/{i:02}.json');packet=frozen['public_checkpoint']
                for arm in arms:
                    key=f'{i:02}-{arm}'
                    if key in state['branches']:continue
                    frozen_req=frozen['request_freeze']['arms'][arm]
                    req=prepare(frozen_req['wire']['messages'],temperature=0)
                    if req.body!=frozen_req['wire'] or req.sha256!=frozen_req['wire_sha256']:raise ValueError('WIRE_MISMATCH')
                    cp=packet['checkpoint_budget'];calls=cp['calls']
                    task=Budget(max_calls=calls+1,max_tokens=cp['max_tokens'],max_tools=cp['max_tools'],wall_seconds=min(600,cp['remaining_seconds']),calls=calls,used_tokens=cp['used_tokens'],tool_calls=cp['tool_calls'])
                    row=dict(request_state='INTENT',task_id=packet['task_id'],arm=arm,wire_sha256=req.sha256,source_budget=cp)
                    state['branches'][key]=row;save(sp,state);save(directory/f'{key}.wire.json',req.body)
                    def durable_send(wire):
                        if hashlib.sha256(wire).hexdigest()!=req.sha256:raise ValueError('WIRE_CHANGED')
                        raw=send(wire,min(90,task.remaining_seconds));save(directory/f'{key}.raw.json',raw);return raw
                    audit=[];transport=SharedTransport(budget,durable_send,authorized=dict(run_id=directory.name,protocol_hash=binding),audit=audit)
                    started=time.monotonic()
                    try:response=transport.send(req,task_budget=task,request_id=key,capability='s22-one-call')
                    finally:save(directory/f'{key}.transport.json',audit)
                    row.update(request_state='RESPONSE_RECEIVED',response=response,request_seconds=time.monotonic()-started);save(sp,state)
                    artifact=delivery(response['text'],response['finish_reason']);save(directory/f'{key}.artifact.json',artifact)
                    # Check restored task limits for every Worker operation as well.
                    budget.task_scope=task
                    result=evaluate(packet['task_id'],artifact['code'],packet['public_cases'])
                    budget.task_scope=None
                    if task.remaining_seconds<=0:raise RuntimeError('BRANCH_TOOL_OR_TIME_BUDGET')
                    u=response['usage']
                    row.update(request_state='COMPLETED',public_pass=result['passed'],public_result=result,
                        action_audit=compare(packet['code'],artifact['code'],response['finish_reason']),
                        reasoning_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens','NOT_REPORTED'),
                        estimated_usd=(u['prompt_tokens']*.3+u['completion_tokens']*1.2)/1e6,
                        actual_invoice=None,task_budget_after=task.snapshot())
                    save(sp,state)
            state.update(status='ONLINE_LOCKED',budget=budget.snapshot());save(sp,state);return state
        except BaseException as exc:
            state.update(status='STOPPED_'+type(exc).__name__,budget=budget.snapshot());save(sp,state);raise

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['check','mock','real']);ap.add_argument('--run-dir');ap.add_argument('--authorization');a=ap.parse_args()
    if a.mode=='check':p,m=verify();print(canonical(dict(status='FROZEN',protocol_hash=p['protocol_hash'],executor_hash=fingerprint(m))));return
    if not a.run_dir:ap.error('--run-dir required')
    result=run(a.run_dir,mode=a.mode,auth=read(a.authorization) if a.authorization else None)
    print(canonical(dict(status=result['status'],branches=len(result['branches']),real_api=a.mode=='real')))
if __name__=='__main__':main()
