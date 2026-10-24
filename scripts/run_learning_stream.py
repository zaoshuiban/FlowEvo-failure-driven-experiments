"""Thin S19 task/batch layer over ExperimentRunner. No API calls on import.

One instance owns ONE G/M/F arm; distinct folders and funded plans are mandatory.
Interrupted tasks/jobs fail closed rather than silently repeating paid requests.
"""
import time
from pathlib import Path
import run_workflow_v2 as e
from failure_evo.contracts import PublicTaskView,PublicFeedback,canonical,fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.repair_choice import generate_rule,choose,RepairChoiceClient
from failure_evo.repair_choice_memory import RuleMemory
from failure_evo.runtime import Budget


def feedback(value):
    if value.get('visibility')!='public':raise ValueError('private feedback forbidden')
    return PublicFeedback(value['status'],value['summary'],tuple(canonical(c) for c in value['public_cases']))


def outcomes(value):
    return {fingerprint([c['input'],c['expected']]):bool(c.get('correct')) for c in value['cases']}


class LearningStream:
    def __init__(self,runner,tasks,*,arm='F',batch_size=10):
        if arm not in ('G','M','F') or batch_size<1:raise ValueError('stream config')
        if len({t['task_id'] for t in tasks})!=len(tasks):raise ValueError('duplicate task')
        self.runner,self.tasks,self.arm,self.batch_size=runner,tasks,arm,batch_size
        self.path=runner.folder;self.log=EvidenceStore(self.path/'stream.jsonl')
        manifest=dict(arm=arm,tasks_hash=fingerprint(tasks),batch_size=batch_size)
        if self.log.records():
            if self.log.records()[0]['payload']!=manifest:raise ValueError('stream changed')
        else:self.log.append('STREAM_OPENED',manifest,time.time())
        self.index=SymptomLearning(self.path/'hypotheses.jsonl',runner.stores[arm],runner.plan['run_id']+'-'+arm)
        self.memory=RuleMemory(self.path/'rule_registry.jsonl')
        self.packets={}
        for p in (self.path/'public_packets').glob('*.json'):self.packets[p.stem]=e.read(p)

    def finalize(self,task,result):
        now=time.time();stream=self.index.stream_id
        for event in result['events']:
            if 'code' not in event:continue
            f=feedback(event['public_feedback'])
            ledger=next((x for x in result.get('candidate_ledger',[]) if x['stage']==event['stage']),{})
            observed=ledger.get('at',now)
            fact=self.runner.stores[self.arm].record(stream_id=stream,task_id=task['task_id'],family_id='unclassified',stage=event['stage'],code=event['code'],feedback=f,observed_at=observed,available_from=now,finish_reason=ledger.get('generation_metadata',{}).get('finish_reason','unknown'),synthetic=self.runner.plan['evidence_kind']=='engineering_fixture')
            if fact:
                packet=dict(task_public=task['task_public'],public_cases=task['public_cases'],code=event['code'],feedback=f.to_dict(),task_id=task['task_id'])
                self.packets[fact['event_id']]=packet;e.write(self.path/'public_packets'/f"{fact['event_id']}.json",packet)
                self.index.ingest(fact,f,event['code'],remaining_calls=self.runner.plan['per_task']['max_calls']-event['budget']['calls'],at=now)
        # Link a public regression to the old hypothesis using this task's new
        # public evidence. Merely failing to solve is not causal harm.
        fresh=[f for f in self.runner.stores[self.arm].visible(now,stream) if f['task_id']==task['task_id']]
        for hook in result.get('hook_events',[]):
            key=hook.get('candidate_id')
            if key and fresh and self.memory.state(key)['permission']=='suspended':
                for h in self.index.states().values():
                    if key in h['linked_operator_versions']:
                        self.index.feedback(h['hypothesis_id'],fresh[0]['event_id'],supports=False,
                            claim='Observed public regression; prior recovery hypothesis requires review',at=now)
        self.log.append('TASK_FINALIZED',dict(task_id=task['task_id'],result_hash=fingerprint(result)),now)

    def assess(self,key,job):
        # Deterministic source selection, never final/private scoring.
        packet=self.packets[job['evidence_ids'][0]];rule=self.memory.state(key)['rule']
        task=PublicTaskView.project(packet['task_public']);f=feedback(packet['feedback'])
        b=Budget(max_calls=2,max_tokens=81920,max_tools=40,wall_seconds=120)
        action=choose(rule,packet['code'],f,b)
        if action=='NATIVE':return None
        if self.runner.judge is None:raise ValueError('real isolated validation evaluator required')
        judge=e.prior.Judge(self.runner.budgets['validation'])
        before=judge.run(packet['task_id'],packet['code'],packet['public_cases'])
        response=RepairChoiceClient(self.runner.transports['validation'],job['job_id']+'/validation').execute_action(action,task,packet['code'],f,b)
        after=judge.run(packet['task_id'],response['code'],packet['public_cases'])
        report=dict(before=before,after=after,response=response,visibility='public',source_task=packet['task_id'])
        path=self.path/'assessments'/f'{key}.json';e.write(path,report)
        if not before.get('cases') or not after.get('cases'):return None
        assessment=self.memory.record_assessment(key,outcomes(before),outcomes(after),report_path=path)
        # The generation format cannot change permissions or execute code itself.
        safe=(choose(rule,packet['code'],PublicFeedback('PUBLIC_PASS'),Budget())=='NATIVE'
              and choose(rule,packet['code'],f,Budget(max_calls=0))=='NATIVE')
        return assessment,safe,packet['task_id']

    def boundary(self,completed):
        if self.arm=='G':return
        if self.arm=='M':
            # M learns only from its own public stream; the normal memory updater
            # owns the same persistent learning budget and diagnostic limits.
            ids=sorted(self.packets)
            if not ids:return
            key=fingerprint(['M',ids])
            if any(r['kind']=='MEMORY_STARTED' and r['payload']['key']==key for r in self.log.records()):return
            self.log.append('MEMORY_STARTED',dict(key=key),time.time())
            self.runner.memory_update(key,{'packets':[self.packets[i] for i in ids]},allow_revision=True)
            return
        known={x['event_id'] for x in self.runner.stores[self.arm].visible(time.time(),self.index.stream_id)}
        with self.memory._transaction() as (rows,_):keys=list(dict.fromkeys(r['candidate_id'] for r in rows))
        for key in keys:
            state=self.memory.state(key)
            if not set(state['evidence_refs'])<=known and state['permission']!='suspended':self.memory.archive(key,'source evidence revoked',harmful=True)
        budget=self.runner.budgets.get('learning')
        available=bool(budget and budget.snapshot()['remaining_calls']>=2 and budget.snapshot()['remaining_cost_microusd']>0)
        for job in self.index.schedule(at=time.time(),budget_available=available):
            # Persist claim BEFORE invoking model; failure/unknown cannot rerun it.
            self.index.start(job,time.time())
            packets=[self.packets[i] for i in job['evidence_ids']]
            h=self.index.states()[job['hypothesis_id']]
            public=dict(hypothesis=h,packets=packets,prior_rules=[self.memory.state(k)['rule'] for k in h['linked_operator_versions']])
            result=generate_rule(self.runner.transports['learning'],public,request_prefix=job['job_id'],limits=e.Limits(),allow_revision=True)
            e.write(self.path/'learning'/f"{job['job_id']}.json",result);self.runner.save()
            key=self.memory.add(result['rule'],job['evidence_ids']) if result['rule'] else None
            if key:
                checked=self.assess(key,job)
                if checked:
                    assessment,safe,source=checked
                    future=[t['task_id'] for t in self.tasks[completed:] if t['task_id']!=source]
                    if assessment['level']=='VERIFIED_BENEFIT' and safe and future and self.runner.plan.get('allow_bounded_trials') is True and self.runner.plan.get('validated_action_safety'):
                        self.memory.authorize(key,tasks=future,opportunities=self.runner.plan.get('trial_opportunities',1),safety_checks=self.runner.plan.get('validated_action_safety',{}),authorization_id=self.runner.plan['protocol_hash'])
            self.index.finish(job,key,time.time());self.runner.save()

    def run(self):
        for i,task in enumerate(self.tasks):
            rows=self.log.records();tid=task['task_id']
            if any(r['kind']=='TASK_FINALIZED' and r['payload']['task_id']==tid for r in rows):
                if (i+1)%self.batch_size==0 or i+1==len(self.tasks):self.boundary(i+1)
                continue
            if any(r['kind']=='TASK_STARTED' and r['payload']['task_id']==tid for r in rows):
                raise ValueError('interrupted task: reconcile saved workflow before resume; never replay paid calls')
            self.log.append('TASK_STARTED',dict(task_id=tid),time.time())
            result=self.runner.solve(self.arm,task)
            if any('error' in x and x.get('request_state')!='NOT_SENT' for x in result['events']):raise ValueError('controller stopped; inspect transport before resume')
            self.finalize(task,result)
            if (i+1)%self.batch_size==0 or i+1==len(self.tasks):self.boundary(i+1)
            self.runner.save()
        self.log.append('ONLINE_LOCKED',dict(task_ids=[t['task_id'] for t in self.tasks]),time.time())


def execute(plan_path,authorization_path,tasks_path,*,resume=False):
    import os,tempfile
    from experiment_s16b2_source import sender_factory
    plan=e.read(plan_path);auth=e.read(authorization_path);tasks=e.read(tasks_path)
    expected=dict(run_id=plan['run_id'],protocol_hash=plan['protocol_hash'],model=plan['model'],budgets=plan['budgets'],allow_real_api=True)
    if auth!=expected or plan['evidence_kind']!='real_experiment':raise PermissionError('new matching API authorization required')
    if plan.get('tasks_sha256')!=e.sha(Path(tasks_path)):raise ValueError('frozen task manifest differs')
    allowed={'task_id','dataset','difficulty','task_public','public_cases','role'}
    if any(set(t)-allowed for t in tasks):raise ValueError('solver manifest contains non-public fields')
    if plan.get('allow_bounded_trials'):
        binding=plan.get('action_safety_report',{})
        report=Path(binding.get('path',''))
        if not report.is_file() or e.sha(report)!=binding.get('sha256'):raise ValueError('bound action safety evidence required')
        safety=e.read(report)
        if (safety.get('representation')!='repair-choice-json-v1' or safety.get('passed') is not True
                or safety.get('checks')!=plan.get('validated_action_safety')
                or set(safety.get('checks',{}))!={'contract','boundary','negative_cases','fallback','no_known_harm'}
                or not all(v is True for v in safety['checks'].values())):raise ValueError('action safety report does not justify trial')
    if plan.get('start_mode')!='cold':raise ValueError('warm-start import is not validated')
    if plan.get('arm') not in ('G','M','F'):raise ValueError('explicit independent arm required')
    if plan['arm']=='F' and not {'solve','learning','validation'}<=set(plan['budgets']):raise ValueError('separate validation and learning budgets required')
    os.environ.update(DOCKER_CONFIG=str(e.ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
    folder=e.ROOT/'runs'/plan['run_id'];runner=e.ExperimentRunner(folder,plan,sender_factory,resume=resume)
    (folder/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(folder/'tmp')
    try:LearningStream(runner,tasks,arm=plan['arm'],batch_size=plan['batch_size']).run()
    finally:runner.save()

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--authorization',required=True);p.add_argument('--tasks',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    execute(a.plan,a.authorization,a.tasks,resume=a.resume)
