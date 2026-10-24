"""Small append-only memory for JSON rules, separate from frozen Python registry.

Assessment inputs are trusted host reports, never model-supplied claims. Public
case comparisons describe local improvement only; trial grants are explicit.
"""
import fcntl
import json
import math
import os
from pathlib import Path
from contextlib import contextmanager
from .contracts import canonical, fingerprint
from .repair_choice import validate_rule, VERSION, choose


def assess(before,after,*,paired=None):
    """Maps stable audited case IDs to bool; require identical case coverage."""
    if not before or set(before)!=set(after) or any(type(x) is not bool for x in [*before.values(),*after.values()]):
        raise ValueError('comparable audited case outcomes required')
    improved=sorted(k for k in before if not before[k] and after[k])
    regressed=sorted(k for k in before if before[k] and not after[k])
    source_success=not all(before.values()) and all(after.values())
    efficiency=False
    if paired is not None:
        # Both must be correct on the SAME frozen review, not merely both fail.
        g=paired['generic'];f=paired['operator'];gc=paired['generic_cost'];fc=paired['operator_full_cost']
        if set(g)!=set(after) or set(f)!=set(after) or f!=after:raise ValueError('paired outcome coverage mismatch')
        if any(type(x) is not bool for x in [*g.values(),*f.values()]):raise ValueError('invalid paired outcomes')
        if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in (gc,fc)):raise ValueError('unknown cost is not zero')
        efficiency=all(g.values()) and all(f.values()) and fc<gc
    return {'level':'VERIFIED_BENEFIT' if source_success or efficiency else 'LOCAL_IMPROVEMENT' if improved and not regressed else 'LEGAL_BEHAVIOR',
            'improved':improved,'regressed':regressed,'source_success':source_success,'paired_efficiency':efficiency,
            'scope':'audited source checks only; no generalization or noninferiority claim'}

class RuleMemory:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)

    @contextmanager
    def _transaction(self):
        with self.path.open('a+',encoding='utf8') as f:
            fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
            rows=[json.loads(line) for line in f if line.strip()]
            def append(row):
                f.seek(0,2);f.write(canonical(row)+'\n');f.flush();os.fsync(f.fileno());rows.append(row)
            yield rows,append

    def _state(self,rows,key):
        matches=[r['state'] for r in rows if r.get('candidate_id')==key]
        if not matches:raise KeyError(key)
        return json.loads(canonical(matches[-1]))

    def add(self,rule,evidence_refs):
        rule=validate_rule(rule)
        if not evidence_refs or any(not isinstance(x,str) or not x for x in evidence_refs):raise ValueError('trusted evidence references required')
        key=fingerprint({'representation':VERSION,'rule':rule,'evidence_refs':sorted(set(evidence_refs))})
        with self._transaction() as (rows,append):
            if any(r.get('candidate_id')==key for r in rows):return key
            append({'event':'CANDIDATE_SAVED','candidate_id':key,'state':{'representation':VERSION,'rule':rule,
                'evidence_refs':sorted(set(evidence_refs)),'generation':'nursery','permission':'shadow',
                'remaining':0,'assessment':None,'used_tasks':[]}})
        return key

    def record_assessment(self,key,before,after,*,report_path,paired=None):
        report=Path(report_path);raw=report.read_text();evaluation=assess(before,after,paired=paired)
        with self._transaction() as (rows,append):
            state=self._state(rows,key)
            state['assessment']=evaluation;state['report']={'path':str(report.resolve()),'hash':fingerprint(raw)}
            if evaluation['regressed']:state['permission']='suspended'
            append({'event':'HOST_ASSESSMENT','candidate_id':key,'state':state})
        return evaluation

    def authorize(self,key,*,tasks,opportunities,safety_checks,authorization_id):
        required={'contract','boundary','negative_cases','fallback','no_known_harm'}
        if set(safety_checks)!=required or not all(v is True for v in safety_checks.values()):raise ValueError('basic verification required')
        if not tasks or len(set(tasks))!=len(tasks) or type(opportunities) is not int or not 1<=opportunities<=5 or not authorization_id:raise ValueError('explicit bounded authorization required')
        with self._transaction() as (rows,append):
            state=self._state(rows,key)
            if state['permission']!='shadow' or state['generation']!='nursery' or not state['assessment'] or state['assessment']['level']!='VERIFIED_BENEFIT':raise ValueError('candidate has no trial eligibility')
            report=state['report']
            if fingerprint(Path(report['path']).read_text())!=report['hash']:raise ValueError('evidence changed')
            state.update(permission='experimental',remaining=opportunities,tasks=list(tasks),authorization_id=authorization_id,safety_checks=safety_checks)
            append({'event':'BOUNDED_TRIAL_AUTHORIZED','candidate_id':key,'state':state})

    def reserve_action(self,key,task_id,code,feedback,budget):
        with self._transaction() as (rows,append):
            s=self._state(rows,key)
            if s['permission']!='experimental' or s['generation']!='nursery' or s['remaining']<=0 or task_id not in s['tasks'] or task_id in s['used_tasks']:return 'NATIVE'
            if fingerprint(Path(s['report']['path']).read_text())!=s['report']['hash']:return 'NATIVE'
            action=choose(s['rule'],code,feedback,budget)
            if action=='NATIVE':return action
            s['remaining']-=1;s['used_tasks'].append(task_id)
            append({'event':'TRIAL_RESERVED','candidate_id':key,'task_id':task_id,'action':action,'state':s})
            return action

    def finish(self,key,task_id,result):
        # Preserve raw host outcome; no automatic promotion or savings inference.
        with self._transaction() as (rows,append):
            s=self._state(rows,key)
            if task_id not in s['used_tasks']:raise ValueError('no reservation')
            if any(r.get('event')=='TRIAL_RESULT' and r.get('candidate_id')==key and r.get('task_id')==task_id for r in rows):raise ValueError('already completed')
            if result.get('visibility') not in (None,'public'):raise ValueError('external review cannot be online feedback')
            before=result.get('before_feedback',{}).get('public_cases',[])
            after=result.get('public_feedback',{}).get('public_cases',[])
            def checks(cases):
                return {fingerprint([c.get('input'),c.get('expected')]):c.get('actual')==c.get('expected') and not c.get('exception_class') for c in cases if 'actual' in c and 'expected' in c}
            a,b=checks(before),checks(after)
            harmed=bool(a and set(a)==set(b) and any(a[k] and not b[k] for k in a))
            if harmed:s.update(permission='suspended',remaining=0)
            append({'event':'TRIAL_RESULT','candidate_id':key,'task_id':task_id,'result':result,'state':s})
            append({'event':'FEEDBACK_DECISION','candidate_id':key,'task_id':task_id,
                    'decision':'SUSPEND' if harmed else 'KEEP','reason':'public case regression' if harmed else 'no certified harm; not a promotion','state':s})

    def archive(self,key,reason,*,harmful=False):
        if not reason:raise ValueError('reason required')
        with self._transaction() as (rows,append):
            s=self._state(rows,key);s.update(permission='suspended' if harmful else 'shadow',generation='cold',remaining=0)
            append({'event':'SUSPENDED' if harmful else 'ARCHIVED','candidate_id':key,'reason':reason,'state':s})

    def propose_relearning(self,key,new_evidence_refs,changed_hypothesis):
        with self._transaction() as (rows,append):
            s=self._state(rows,key);new=sorted(set(new_evidence_refs)-set(s['evidence_refs']))
            if not new or not changed_hypothesis.strip():raise ValueError('new trusted evidence and changed hypothesis required')
            # Scheduling proposal only: never retries, spends, or restores old permission.
            append({'event':'RELEARNING_PROPOSED','candidate_id':key,'new_evidence_refs':new,
                           'changed_hypothesis':changed_hypothesis,'state':s})

    def state(self,key):
        with self._transaction() as (rows,_):return self._state(rows,key)


def run_trial(memory,key,client,task,code,feedback,budget,evaluate):
    """Explicit real-run entry. Native fallback remains caller-owned and budgeted."""
    action=memory.reserve_action(key,task.problem_id,code,feedback,budget)
    if action=='NATIVE':return {'status':'declined','fallback':'NATIVE','code':code}
    try:result=client.attempt(action,task,code,feedback,budget,evaluate)
    except Exception as exc:
        memory.finish(key,task.problem_id,{'status':'error','exception':type(exc).__name__})
        raise  # unknown sends cannot silently become a free retry
    memory.finish(key,task.problem_id,result)
    return result
