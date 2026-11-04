"""Amended continuation: immutable parent, no retry of missing89, remaining budgets."""
import sys, time, shutil, fcntl, math
from pathlib import Path
from run_math_stream200_exploratory import *
from failure_evo import math_stream as ms
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.evidence import EvidenceStore
PARENT=ROOT/'runs/math_stream200_exploratory_20261102_01'
OUT=ROOT/'runs/math_stream200_resume90_20261102_01'
RID='R/89/omni-hard200-row-111/base/s1'
BASE_BUDGET=ms.budget

def remaining_budget(path,run,ph,*,calls,tools=0):
    path=Path(path)
    # Only lifetime solve/tool accounts carry a balance; future learning windows
    # have distinct, not previously consumed, frozen per-window accounts.
    rel=path.relative_to(OUT)
    parent=PARENT/rel
    if len(rel.parts)!=2 or not parent.exists():return BASE_BUDGET(path,run,ph,calls=calls,tools=tools)
    b=PersistentBudget.__new__(PersistentBudget);b.path=parent
    with b._locked() as rows:
        cfg=rows[0]['payload']['config'];tot=b._totals(rows);deadline=rows[0]['payload']['deadline']
    manifest=read(OUT/'continuation.json');limits=manifest['balances'][str(rel)]
    kw={k:v for k,v in cfg.items() if k not in ('run_id','protocol_hash','currency','cost_unit')}
    kw.update(limits)
    return PersistentBudget(path,run_id=run,protocol_hash=ph,**kw)

class Continuation(StreamRuntime):
    def evidence(self,arm,cutoff):
        a=self.arms[arm];tasks={t.task_id:t for t in self.tasks};out=[]
        locks={r['payload']['id']:r['payload']['lock'] for r in a['states'].records() if r['kind']=='ANSWER_LOCKED'}
        for r in a['states'].records():
            p=r['payload']
            if r['kind']!='PRIVATE_SCORED' or p['sequence']==89 or p['sequence']>cutoff or p['verdict']['status']!='CONFIRMED_WRONG':continue
            l=locks[p['id']]
            if not l['responses'] or l['responses'][-1]['finish_reason']!='stop':continue
            out.append(dict(event_id=fingerprint([p['id'],p['verdict']['locked_sha256']]),sequence=p['sequence'],task=tasks[p['task_id']].to_dict(),correct=False,final_output=l['final_output'],trajectory=l['responses'],locked_sha256=l['locked_sha256']))
        return out
    def history_packet(self,arm,cutoff):
        packet,refs=super().history_packet(arm,cutoff)
        bad=self.tasks[88]
        packet['questions']=[q for q in packet['questions'] if q['problem']!=bad.problem]
        if arm=='F':packet['observations']=[o for o in packet['observations'] if o['problem']!=bad.problem]
        if bad.task_id in refs['task_ids']:
            refs['task_ids'].remove(bad.task_id);refs['omitted_task_ids'].append(bad.task_id)
        return packet,refs
    def run(self):
        with (self.path/'stream.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);self.health()
            for seq in range(90,201):
                task=self.tasks[seq-1];locks={};order=ms.ARMS[(seq-1)%4:]+ms.ARMS[:(seq-1)%4]
                for arm in order:self.health();locks[arm]=self.solve(arm,task,seq)
                for arm in ms.ARMS:
                    a=self.arms[arm];eid=f'{arm}/{seq}/{task.task_id}';v=a['scorer'].score(task,locks[arm])
                    self.emit_once(a['states'],'PRIVATE_SCORED',eid,dict(task_id=task.task_id,sequence=seq,verdict=v))
                print(f'Task {seq}/200 locked and scored in all four arms',flush=True)
                if seq%20==0:
                    for arm in ('T','F'):
                        if seq<200:self.arms[arm]['learner'].learn(seq)
                    for a in self.arms.values():self.emit_once(a['states'],'WINDOW_COMPLETED',str(seq),dict(cutoff_sequence=seq))
                    self.emit_once(self.events,'WINDOW_COMPLETED',str(seq),dict(cutoff_sequence=seq))
                    save(self.path/'progress.json',dict(last_original_sequence=seq,completed_comparable_tasks=seq-1,missing_sequences=[89],status='COMPLETE_WITH_MISSING' if seq==200 else 'RUNNING'))
            self.emit_once(self.events,'STREAM_COMPLETED','complete',dict(tasks=199,missing=[89],paid_api=True,protocol_amended=True))

def prepare():
    if (OUT/'READY').exists():return
    if OUT.exists():raise RuntimeError('partial preparation; inspect before removing or restarting')
    old=read(PARENT/'execution_plan.json')
    assert all(sha(ROOT/k)==v for k,v in old['sources'].items()),'parent source drift'
    balances={};pending=[]
    for p in PARENT.rglob('*budget.jsonl'):
        b=PersistentBudget.__new__(PersistentBudget);b.path=p
        with b._locked() as rows:
            states,_=b._state(rows);tot=b._totals(rows);cfg=rows[0]['payload']['config']
            pending += [k for k,v in states.items() if v['status']!='settled']
            if len(p.relative_to(PARENT).parts)==2:
                limits={k:cfg[k]-tot[t] for k,t in [('max_calls','calls'),('max_tokens','tokens'),('max_tools','tools'),('max_cost_microusd','cost'),('max_tool_milliseconds','tool_ms')]}
                limits['wall_seconds']=max(1,math.floor(rows[0]['payload']['deadline']-time.time()))
                balances[str(p.relative_to(PARENT))]=limits
    assert pending==[RID],pending
    for arm in ms.ARMS:
        rows=EvidenceStore(PARENT/arm/'task_state.jsonl').records()
        assert [r['payload']['sequence'] for r in rows if r['kind']=='PRIVATE_SCORED']==list(range(1,89))
        assert not any(r['kind'] in ('MATH_SHADOW','MATH_ROUTER_PUBLICATION') for r in EvidenceStore(PARENT/arm/'registry.jsonl').records()),'candidate migration needs explicit review'
    manifest=dict(parent=str(PARENT),parent_files={str(p.relative_to(PARENT)):sha(p) for p in PARENT.rglob('*') if p.is_file()},start=90,missing=[89],unknown=RID,balances=balances,old_costs_not_zero=True)
    OUT.mkdir();save(OUT/'continuation.json',manifest)
    plan=dict(old);plan.update(mode='AMENDED_CONTINUATION90_SHADOW_ONLY',continuation_sha256=fingerprint(manifest))
    plan['sources']=dict(old['sources']);plan['sources'][str(Path(__file__).relative_to(ROOT))]=sha(__file__)
    save(OUT/'execution_plan.json',plan);save(OUT/'lineage.json',read(PARENT/'lineage.json'))
    for arm in ms.ARMS:
        d=OUT/arm;d.mkdir()
        # Import only completed prefix states, not request caches or unresolved ledgers.
        for name in ['task_state.jsonl','controller.jsonl','scores.jsonl','registry.jsonl']:
            src=EvidenceStore(PARENT/arm/name);dest=EvidenceStore(d/name)
            for r in src.records():
                v=r['payload'];seq=v.get('sequence',v.get('lock',{}).get('sequence',0))
                if name=='controller.jsonl':continue # no replay of prefix solve/score is needed
                if seq==89:continue
                dest.append(r['kind'],v,r['at'])
        eid=f'{arm}/89/{lines(DATA/"public/tasks.jsonl")[88]["task_id"]}'
        EvidenceStore(d/'task_state.jsonl').append('PRIVATE_SCORED',dict(id=eid,task_id=lines(DATA/'public/tasks.jsonl')[88]['task_id'],sequence=89,verdict=dict(status='INFRASTRUCTURE_MISSING',correct=None,credible_failure=False,reason='AMENDED_EXCLUSION_NOT_A_MATH_SCORE')),time.time())
        src=PARENT/arm/'learning'
        if src.exists():shutil.copytree(src,d/'learning')
    (OUT/'READY').write_text('Preparation completed; no new API request.\n')

def main():
    prepare();manifest=read(OUT/'continuation.json')
    assert all(sha(PARENT/k)==v for k,v in manifest['parent_files'].items()),'parent changed'
    plan=read(OUT/'execution_plan.json')
    assert all(sha(ROOT/k)==v for k,v in plan['sources'].items()),'continuation source changed'
    if '--prepare-only' in sys.argv:print('READY: no API sent; remaining budgets frozen; parent UNKNOWN retained');return
    ms.budget=remaining_budget
    s=Continuation(OUT,plan,lines(DATA/'public/tasks.jsonl'),lines(DATA/'private/scoring.jsonl'),read(OUT/'lineage.json'),backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),learner_factory=lambda st,a:WindowLearner(st,a))
    for a in s.arms.values():a['scorer']=QuarantinedScorer(a['scorer'],plan['scoring_quarantine'])
    try:s.run()
    except BaseException as exc:
        EvidenceStore(OUT/'stops.jsonl').append('STOP',dict(type=type(exc).__name__,reason=str(exc),no_resend=True),time.time());raise
    finally:
        summarize(OUT)
        save(OUT/'cost_scope.json',dict(note='Continuation summary includes imported learning accounts but excludes parent solver costs; never interpret it as entire experiment cost.',parent_summary=str(PARENT/'summary.json'),unknown_retained=RID))
if __name__=='__main__':main()
