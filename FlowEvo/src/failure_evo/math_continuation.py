"""Explicit cumulative continuation, immutable parent and inclusive budgets.

Only an incomplete solver task may be isolated. No learning UNKNOWN, new Gate
privilege, request replay, budget reset, or mathematical outcome selection.
"""
import copy,fcntl,json,shutil,time,hashlib
from pathlib import Path
from .contracts import fingerprint
from .evidence import EvidenceStore
from .persistent_budget import PersistentBudget
from .math_stream import read,save,sha,ARMS,budget
from .network_transport import validate_policy
from .run_health import RunUnhealthy

VERSION='cumulative-solver-isolation-v1'

def account(path):
    b=PersistentBudget.__new__(PersistentBudget);b.path=Path(path)
    with b._locked() as rows:
        return rows[0]['payload'],b._state(rows)[0],b._totals(rows)

def files(root):
    return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}

def verify(path,plan):
    path=Path(path);binding=plan['continuation_binding'];m=read(path/'continuation.json')
    if m['version']!=VERSION or fingerprint(m)!=binding['sha256']:raise RunUnhealthy('continuation manifest changed')
    parent=Path(m['parent'])
    if files(parent)!=m['parent_files']:raise RunUnhealthy('immutable parent changed')
    old=read(parent/'execution_plan.json')
    # Scientific task/order/learning/Gate/budget protocol remains exactly the same.
    for k in (set(old)|set(plan))-{'sources','network_policy','continuation_binding'}:
        if old.get(k)!=plan.get(k):raise RunUnhealthy('continuation changed frozen research field: '+k)
    for rel,item in m['inherited_prefixes'].items():
        p=path/rel
        with p.open('rb') as f:data=f.read(item['bytes'])
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise RunUnhealthy('inherited journal prefix changed: '+rel)
    for q in m['isolations']:
        _,states,_=account(path/q['ledger']);r=states.get(q['request_id'],{})
        if r.get('status')!='unknown' or fingerprint(r)!=q['state_sha256']:raise RunUnhealthy('isolated UNKNOWN changed')
        events=EvidenceStore(path/q['arm']/'requests.jsonl').records()
        if any(x['kind']=='RAW_RESPONSE' and x['payload'].get('request_id')==q['request_id'] for x in events):raise RunUnhealthy('isolated request has response')
    return m

def inherited_budget_factory(path,plan):
    path=Path(path);m=verify(path,plan)
    def make(p,run,ph,*,calls,tools=0):
        rel=str(Path(p).relative_to(path))
        if rel not in m['account_configs']:return budget(p,run,ph,calls=calls,tools=tools)
        cfg=m['account_configs'][rel]
        # Same journal, identity, original deadline, limits and reservations.
        # Existing spend is not subtracted from a new ledger or counted twice.
        args={k:v for k,v in cfg.items() if k not in ('currency','cost_unit')}
        return PersistentBudget(p,**args)
    return make

def prepare(parent,out,*,isolate_sequence,sources,worker_manifest,network_policy):
    parent=Path(parent).resolve();out=Path(out).resolve()
    if out.exists() or parent==out or parent in out.parents:raise PermissionError('new separate continuation directory required')
    with (parent/'stream.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        old=read(parent/'execution_plan.json')
        if 'cumulative' not in old:raise PermissionError('only cumulative streams supported')
        if old.get('continuation_binding'):verify(parent,old)
        if old['cumulative_worker_manifest']!=worker_manifest:raise PermissionError('Worker drift')
        for ref in list(old['cumulative_input_bindings'].values())+[old['gate_pool_binding']] if old.get('gate_pool_binding') else list(old['cumulative_input_bindings'].values()):
            if sha(Path(ref['path']))!=ref['sha256']:raise PermissionError('frozen data drift')
        # Old runtime code may differ, but its saved source must remain verifiable.
        for rel,digest in old['sources'].items():
            if sha(parent/'frozen_source'/rel)!=digest:raise PermissionError('parent frozen source missing or changed: '+rel)
        tasks=[json.loads(x) for x in Path(old['cumulative_input_bindings']['tasks']['path']).read_text().splitlines()]
        n=isolate_sequence
        if type(n) is not int or not 1<=n<len(tasks):raise PermissionError('isolate one incomplete nonterminal task')
        stream=EvidenceStore(parent/'stream.jsonl').records()
        done=[r['payload']['sequence'] for r in stream if r['kind']=='CUMULATIVE_BOUNDARY_COMPLETED']
        if done!=list(range(1,n)):raise PermissionError('not the next unfinished task')
        prior=read(parent/'continuation.json')['isolations'] if old.get('continuation_binding') else []
        known={(q['ledger'],q['request_id']) for q in prior};pending=[];configs={};totals={}
        for p in parent.rglob('*budget.jsonl'):
            opened,states,total=account(p);rel=str(p.relative_to(parent));configs[rel]=opened['config'];totals[rel]=total
            if time.time()>=opened['deadline']:raise PermissionError('inherited budget deadline expired')
            for rid,r in states.items():
                if r['status'] not in ('settled','not_sent') and (rel,rid) not in known:pending.append((rel,rid,r))
        if len(pending)!=1:raise PermissionError('exactly one new solver UNKNOWN required')
        rel,rid,state=pending[0];arm=rel.split('/')[0]
        if rel!=arm+'/solve_budget.jsonl' or arm not in ARMS or state['status']!='unknown' or not rid.startswith(f'{arm}/{n}/{tasks[n-1]["task_id"]}/'):
            raise PermissionError('only the unfinished solver task can be isolated')
        req=[r for r in EvidenceStore(parent/arm/'requests.jsonl').records() if r['payload'].get('request_id')==rid]
        if sum(r['kind']=='SEND_STARTED' for r in req)!=1 or any(r['kind']=='RAW_RESPONSE' for r in req):raise PermissionError('unambiguous absent solver response required')
        stop=EvidenceStore(parent/'stops.jsonl').records()[-1]['payload']
        if stop.get('type') not in ('gaierror','TimeoutError','RemoteDisconnected','ConnectionResetError','SSLEOFError','IncompleteRead','SendUnknown'):
            raise PermissionError('stop is not a recorded transport interruption')
        for a in ARMS:
            rr=EvidenceStore(parent/a/'task_state.jsonl').records()
            if [r['payload']['sequence'] for r in rr if r['kind']=='PRIVATE_SCORED']!=list(range(1,n)):
                raise PermissionError('task already scored or prior prefix inconsistent')
            if any(r['payload'].get('sequence',0)>n for r in rr):raise PermissionError('future task started')
            # Algorithm library migration has separate evidence/permission concerns.
            if any(r['kind'] in ('MATH_SHADOW','MATH_EXPERIMENTAL','MATH_ROUTER_PUBLICATION') for r in EvidenceStore(parent/a/'registry.jsonl').records()):
                raise PermissionError('artifact migration needs independent review; not automated here')
        q=dict(sequence=n,task_id=tasks[n-1]['task_id'],arm=arm,ledger=rel,request_id=rid,state_sha256=fingerprint(state),
               wire_sha256=state['request_hash'],reserved_upper_microusd=state['cost_upper_microusd'],status='UNKNOWN',no_resend=True)
        before=files(parent);out.mkdir(parents=True)
        prefixes={}
        for a in ARMS:
            for p in (parent/a).rglob('*'):
                if not p.is_file():continue
                if p.is_symlink():raise PermissionError('symlink in inherited state')
                dest=out/p.relative_to(parent);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
                if p.suffix not in ('.lock',):prefixes[str(dest.relative_to(out))]=dict(bytes=p.stat().st_size,sha256=sha(p))
        m=dict(version=VERSION,parent=str(parent),parent_files=before,parent_protocol_sha256=fingerprint(old),
               start_sequence=n+1,missing_sequences=[x['sequence'] for x in prior]+[n],isolations=prior+[q],
               inherited_prefixes=prefixes,account_configs=configs,inherited_totals=totals,
               current_sources=sources,network_policy=validate_policy(network_policy),
               budget_scope='All original spend and UNKNOWN reservations remain in inherited accounts. No limit or deadline reset.',
               authorization_scope='Continuation requires its own run/protocol grant within the unchanged original total ceiling.')
        save(out/'continuation.json',m)
        plan=copy.deepcopy(old);plan.update(sources=sources,network_policy=validate_policy(network_policy),continuation_binding=dict(sha256=fingerprint(m)))
        save(out/'execution_plan.json',plan)
        # Preserve old stream separately; new hash chain explicitly identifies the import.
        shutil.copyfile(parent/'stream.jsonl',out/'parent_stream.snapshot')
        events=EvidenceStore(out/'stream.jsonl');events.append('STREAM_FROZEN',plan,stream[0]['at'])
        for r in stream[1:]:events.append(r['kind'],r['payload'],r['at'])
        now=time.time()
        events.append('CONTINUATION_IMPORTED',dict(parent=str(parent),manifest_sha256=fingerprint(m),excluded_sequence=n),now)
        for a in ARMS:
            rows=EvidenceStore(out/a/'task_state.jsonl')
            rows.append('PRIVATE_SCORED',dict(id=f'{a}/{n}/{tasks[n-1]["task_id"]}',task_id=tasks[n-1]['task_id'],sequence=n,
                verdict=dict(status='INFRASTRUCTURE_MISSING',correct=None,credible_failure=False,reason='ISOLATED_UNKNOWN_NOT_MATH_FAILURE')),now)
            if n%plan['window']==0:
                if a in ('T','F'):
                    count=sum(t['calls'] for rel,t in totals.items() if rel.startswith(a+'/learning/'+str(n)+'/'))
                    save(out/a/'learning'/str(n)/'result.json',dict(status='CUMULATIVE_WINDOW_ACCOUNTED',learning_calls=count,cutoff=n))
                rows.append('WINDOW_COMPLETED',dict(id=str(n),cutoff_sequence=n),now)
        if n%plan['window']==0:events.append('WINDOW_COMPLETED',dict(id=str(n),cutoff_sequence=n),now)
        events.append('CUMULATIVE_BOUNDARY_COMPLETED',dict(id=str(n),sequence=n,infrastructure_missing=True),now)
        save(out/'progress.json',dict(last_sequence=n,completed_comparable_tasks=n-len(m['missing_sequences']),missing_sequences=m['missing_sequences'],status='PREPARED_CONTINUATION_NOT_STARTED'))
        auth=dict(run_id=out.name,protocol_sha256=fingerprint(plan),paid_api_authorized=False,
            max_cost_microusd=plan['budget_freeze']['total_reserved_upper_microusd'],max_model_calls=plan['budget_freeze']['total_model_calls_upper'],
            note='Inclusive original experiment ceiling, not a new allowance. All parent spend and UNKNOWN retained.')
        save(out/'authorization_template.json',auth)
        source_root=Path(__file__).resolve().parents[3]
        for rel,digest in sources.items():
            p=source_root/rel
            if sha(p)!=digest:raise PermissionError('source changed during preparation')
            dest=out/'frozen_source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        if files(parent)!=before:raise PermissionError('parent changed during preparation')
        verify(out,plan)
        (out/'READY').write_text('Zero API prepared; explicit continuation authorization required.\n')
        return m
