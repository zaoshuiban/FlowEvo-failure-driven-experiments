"""Prepare/run the opt-in amended network-isolation protocol; no automatic old resend."""
import argparse,math,shutil,time
from pathlib import Path
from run_math_stream200_exploratory import *
from failure_evo import math_stream as ms
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.evidence import EvidenceStore
from math_stream_recovery_v3 import ResilientStream,account,report_chain
PARENTS=[ROOT/'runs/math_stream200_exploratory_20261102_01',ROOT/'runs/math_stream200_resume90_20261102_01',ROOT/'runs/math_stream200_resilient113_20261102_02',ROOT/'runs/math_stream200_dns116_20261102_02']
OUT=ROOT/'runs/math_stream200_finish196_20261103_01'
BASE=ms.budget

def remaining_budget(path,run,ph,*,calls,tools=0):
    path=Path(path);rel=str(path.relative_to(OUT));m=read(OUT/'continuation.json')
    if rel not in m['accounts']:return BASE(path,run,ph,calls=calls,tools=tools)
    cfg=m['accounts'][rel]['remaining_config'];kw={k:v for k,v in cfg.items() if k not in ('run_id','protocol_hash','currency','cost_unit')}
    return PersistentBudget(path,run_id=run,protocol_hash=ph,**kw)

def prepare():
    if (OUT/'READY').exists():return
    if OUT.exists():raise RuntimeError('partial preparation: audit before any retry')
    parent=PARENTS[-1];old=read(parent/'execution_plan.json')
    if not all(sha(ROOT/k)==v for k,v in old['sources'].items()):raise PermissionError('parent frozen source changed')
    pp=read(parent/'continuation.json')
    for ancestor in pp['parents']:
        if not all(sha(Path(ancestor['root'])/k)==v for k,v in ancestor['files'].items()):raise PermissionError('ancestor changed')
    manifests=[dict(root=str(p),files={str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}) for p in PARENTS]
    balances={};pending=[];deadlines=[]
    for p in parent.rglob('*budget.jsonl'):
        opened,states,tot=account(p);cfg=opened['config']
        pending += [k for k,s in states.items() if s['status']!='settled']
        if len(p.relative_to(parent).parts)==2:
            remaining=dict(cfg)
            for field,t in [('max_calls','calls'),('max_tokens','tokens'),('max_tools','tools'),('max_cost_microusd','cost'),('max_tool_milliseconds','tool_ms')]:remaining[field]-=tot[t]
            remaining['wall_seconds']=max(1,math.floor(opened['deadline']-time.time()));deadlines.append(opened['deadline'])
            balances[str(p.relative_to(parent))]=dict(parent_config=cfg,parent_totals=tot,remaining_config=remaining)
    expected={'G/151/omni-hard200-row-3806/base/s0','R/194/omni-hard200-row-3811/base/s0','F/195/omni-hard200-row-3945/base/s0'}
    if set(pending)!=expected:raise PermissionError('unexpected unresolved requests')
    stop=EvidenceStore(parent/'stops.jsonl').records()[-1]['payload']
    if stop.get('reason')!='isolation ceiling reached; new UNKNOWN retained':raise PermissionError('unexpected stop')
    for rid in expected:
        arm=rid.split('/')[0]
        req=[r for r in EvidenceStore(parent/arm/'requests.jsonl').records() if r['payload'].get('request_id')==rid]
        if any(r['kind']=='RAW_RESPONSE' for r in req) or sum(r['kind']=='SEND_STARTED' for r in req)!=1:raise PermissionError('ambiguous request')
        finished=[r['payload'] for r in req if r['kind']=='REQUEST_FINISHED']
        if not finished or finished[-1].get('audit',[])[-1].get('status')!='UNKNOWN':raise PermissionError('unknown audit mismatch')
        _,states,_=account(parent/arm/'solve_budget.jsonl')
        if states[rid]['status']!='unknown':raise PermissionError('unknown state mismatch')
    qs=[r['payload']['sequence'] for r in EvidenceStore(parent/'network_isolation.jsonl').records() if r['kind']=='NETWORK_ISOLATED']
    if qs!=[151,194]:raise PermissionError('prior isolations differ')
    unknowns=pp['unknown_requests']+sorted(expected)
    for arm in ms.ARMS:
        rows=EvidenceStore(parent/arm/'task_state.jsonl').records();sc=[r['payload'] for r in rows if r['kind']=='PRIVATE_SCORED']
        if [x['sequence'] for x in sc]!=list(range(1,195)):raise PermissionError('parent prefix differs')
        if sum(x['verdict']['status']=='INFRASTRUCTURE_MISSING' for x in sc)!=5:raise PermissionError('parent missing differs')
        if any(r['kind'] in ('MATH_SHADOW','MATH_ROUTER_PUBLICATION') for r in EvidenceStore(parent/arm/'registry.jsonl').records()):raise PermissionError('nonempty artifact library requires migration review')
    if time.time()>=min(deadlines):raise PermissionError('parent budget wall limit expired')
    OUT.mkdir();manifest=dict(parents=manifests,accounts=balances,start=196,missing=[89,112,115,151,194,195],unknown_requests=unknowns)
    save(OUT/'continuation.json',manifest)
    plan=dict(old);plan['sources']=dict(old['sources'])
    for f in [Path(__file__).resolve(),ROOT/'scripts/math_stream_recovery_v3.py']:
        plan['sources'][str(f.relative_to(ROOT))]=sha(f)
    plan.update(mode='AMENDED_NETWORK_ISOLATION_EXPLORATION',continuation_sha256=fingerprint(manifest),recovery=dict(version='finish196-explicit-amendment-no-new-isolations',start=196,inherited_missing=[89,112,115,151,194,195],max_new_isolations=0,consecutive_missing_stop=True,expires_at=min(deadlines),network_scope='solver transport only, before any task score, one identified sent UNKNOWN without RAW_RESPONSE',learning_network_failure='GLOBAL_STOP',no_retry=True))
    save(OUT/'execution_plan.json',plan);save(OUT/'lineage.json',read(parent/'lineage.json'))
    for arm in ms.ARMS:
        d=OUT/arm;d.mkdir()
        for name in ['task_state.jsonl','scores.jsonl','controller.jsonl','registry.jsonl']:
            for r in EvidenceStore(parent/arm/name).records():
                seq=r['payload'].get('sequence',0)
                if seq==195:continue
                EvidenceStore(d/name).append(r['kind'],r['payload'],r['at'])
        task=lines(DATA/'public/tasks.jsonl')[194]
        EvidenceStore(d/'task_state.jsonl').append('PRIVATE_SCORED',dict(id=f'{arm}/195/{task["task_id"]}',task_id=task['task_id'],sequence=195,verdict=dict(status='INFRASTRUCTURE_MISSING',correct=None,credible_failure=False,reason='INHERITED_NETWORK_UNKNOWN_NO_MATH_EVALUATION')),time.time())
        src=parent/arm/'learning'
        if src.exists():shutil.copytree(src,d/'learning')
    (OUT/'READY').write_text('Prepared only. No paid API calls.\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','summary']);args=p.parse_args()
    prepare();m=read(OUT/'continuation.json')
    for parent in m['parents']:
        if not all(sha(Path(parent['root'])/k)==v for k,v in parent['files'].items()):raise PermissionError('immutable parent changed')
    plan=read(OUT/'execution_plan.json')
    if not all(sha(ROOT/k)==v for k,v in plan['sources'].items()):raise PermissionError('source drift')
    if args.action=='prepare':print('READY; starts196; prior189 completed; 6 missing; no API sent');return
    if args.action=='summary':print(report_chain(PARENTS+[OUT],OUT/'chain_report'));return
    if not configured_api_key():raise PermissionError('DeepSeek credential unavailable')
    ms.budget=remaining_budget
    s=ResilientStream(OUT,plan,lines(DATA/'public/tasks.jsonl'),lines(DATA/'private/scoring.jsonl'),read(OUT/'lineage.json'),backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),learner_factory=lambda st,a:WindowLearner(st,a))
    for a in s.arms.values():a['scorer']=QuarantinedScorer(a['scorer'],plan['scoring_quarantine'])
    try:s.run()
    except BaseException as exc:
        EvidenceStore(OUT/'stops.jsonl').append('GLOBAL_STOP',dict(type=type(exc).__name__,reason=str(exc),no_resend=True),time.time());raise
    finally:
        report_chain(PARENTS+[OUT],OUT/'chain_report')
if __name__=='__main__':main()
