"""One chronological ALFWorld learning controller, default paid dispatch off."""
from dataclasses import asdict
import json
from pathlib import Path
import time

from alfworld_.audited_baseline import AuditedActionClient, classify_trace
from alfworld_.failure_learning import (
    VERSION,EnvironmentCompilerAdapter,EnvironmentPolicyRunner,create_candidate,import_episode,
)
from alfworld_.learning_runtime import execute_episode,validate_and_publish
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator,FailureOperatorRegistry
from failure_evo.math_stream import read,save,sha
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import assert_run_healthy,RunUnhealthy


def account(path,run_id,ph,*,calls,tokens,cost,tools=0):
    return PersistentBudget(path,run_id=run_id,protocol_hash=ph,max_calls=calls,max_tokens=tokens,
        max_tools=tools,max_cost_microusd=cost,token_rate_microusd_per_million=1200000,
        tool_cost_upper_microusd=0,max_tool_milliseconds=tools*15000,tool_milliseconds_upper=15000,
        wall_seconds=7*86400)


class LearningStream:
    def __init__(self,root,plan,backend,*,engineering=False,sender=None):
        self.root,self.plan,self.backend=Path(root),plan,backend
        self.engineering,self.sender=engineering,sender
        self.ph=fingerprint(plan)
        self.run_id=('engineering:' if engineering else '')+plan['run_id']
        self.store=FailureEvidenceStore(self.root/'failures.jsonl')
        self.views=EvidenceStore(self.root/'failure_views.jsonl')
        self.events=EvidenceStore(self.root/'stream.jsonl')
        self.registry=FailureOperatorRegistry(self.root/'registry.jsonl',self.store)
        self.actions=account(self.root/'action_budget.jsonl',self.run_id+':actions',self.ph,
                             calls=plan['action_calls'],tokens=plan['action_calls']*11024,cost=plan['max_cost_microusd']-400_000)
        self.tools=account(self.root/'worker_budget.jsonl',self.run_id+':worker',self.ph,
                           calls=0,tokens=0,cost=0,tools=plan['worker_calls'])
        self.runner=EnvironmentPolicyRunner(backend,self.root/'worker.jsonl',self.tools)
        self.job_budgets=[]
        for path in self.root.glob('jobs/*/budget.jsonl'):
            slot=path.parent.name
            if slot not in ('0','1'):
                raise PermissionError('unknown learning budget shard')
            self.job_budgets.append(account(path,self.run_id+':learning:'+slot,self.ph,
                                           calls=2,tokens=2*73728,cost=200000))

    def health(self):
        accounts=[self.actions,self.tools,*self.job_budgets]
        assert_run_healthy(budgets=accounts,network_policy=self.plan['network_policy'] if not self.engineering else None)
        for path in self.root.rglob('provider.jsonl'):
            rows=EvidenceStore(path).records()
            if any(r['kind']=='SEND_UNKNOWN' for r in rows):
                raise RunUnhealthy('unknown learning request')
            started={r['payload']['key'] for r in rows if r['kind']=='SEND_STARTED'}
            received={r['payload']['key'] for r in rows if r['kind']=='RAW_RESPONSE'}
            if started-received:
                raise RunUnhealthy('unfinished learning dispatch')

    def client(self,prefix):
        return AuditedActionClient(self.root/'clients'/prefix,self.actions,self.plan,
                                   sender=(lambda wire:self.sender('action',wire)) if self.engineering else None,request_prefix=prefix+'/')

    def ingest_history(self,source_root):
        protocol=read(source_root/'protocol.json')
        requests={r['payload']['request_id']:r['payload'] for r in EvidenceStore(source_root/'requests.jsonl').records()
                  if r['kind']=='ACTION_RESPONSE'}
        request_wires={r['payload']['request_id']:r['payload']['wire'] for r in EvidenceStore(source_root/'requests.jsonl').records()
                       if r['kind']=='ACTION_REQUEST'}
        rows={r['task_id']:r for r in protocol['tasks']}
        for event in EvidenceStore(source_root/'episodes.jsonl').records():
            if event['kind']!='EPISODE_LOCKED':
                continue
            tid=event['payload']['task_id']
            initial=request_wires.get(tid+'/0',{}).get('messages',[{},{}])[-1].get('content','')
            observation=initial.split('Current observation:\n')[-1].split('\nValid actions')[0].strip()
            import_episode(self.store,self.views,stream_id=self.run_id,row=rows[tid],event=event,
                           requests=requests,initial_observation=observation,available_from=time.time())

    def learn(self,after_sequence):
        self.health()
        prior=[r['payload'] for r in self.events.records() if r['kind']=='LEARNING_STARTED']
        if len(prior)>=self.plan['max_candidates']:
            return dict(status='LEARNING_LIMIT_REACHED')
        facts=list(self.store.visible(time.time(),self.run_id))
        used={eid for p in prior for eid in p['evidence_ids']}
        fresh=[f for f in facts if f['event_id'] not in used]
        if not fresh:
            return dict(status='NO_NEW_TRUSTED_FAILURE')
        # A bounded historical shortlist is not a common-mechanism assertion.
        ids=self.select_evidence(fresh)
        slot=len(prior)
        payload=dict(slot=slot,evidence_ids=ids,after_sequence=after_sequence,
                     all_candidate_ids=[f['event_id'] for f in facts],selection='newest-and-earliest-unassociated-v1')
        self.events.append('LEARNING_STARTED',payload,time.time())
        return self._complete_learning(payload)

    def select_evidence(self,fresh):
        selected=[fresh[-1]]+fresh[:2]
        return list(dict.fromkeys(f['event_id'] for f in selected))

    def _complete_learning(self,payload):
        slot=payload['slot']
        folder=self.root/'jobs'/str(slot)
        b=account(folder/'budget.jsonl',self.run_id+':learning:'+str(slot),self.ph,
                  calls=2,tokens=2*73728,cost=200000)
        if not any(old.path==b.path for old in self.job_budgets):
            self.job_budgets.append(b)
        auth=dict(run_id=b.config['run_id'],protocol_hash=self.ph,model='deepseek-flash',protocol=VERSION,
                  max_cost_microusd=b.config['max_cost_microusd'],paid_api_authorized=True)
        provider=EnvironmentCompilerAdapter(folder/'provider.jsonl',b,model='deepseek-flash',authorization=auth,
                   mock=self.engineering,sender=(lambda wire:self.sender('learning',wire)) if self.engineering else None,
                   network_policy=self.plan['network_policy'] if not self.engineering else None)
        compiler=BoundedCompiler(provider,b,folder/'compiler.jsonl','deepseek-flash',max_input_upper=32768)
        result=create_candidate(folder,compiler,self.store,self.views,stream_id=self.run_id,
                   evidence_ids=payload['evidence_ids'],worker_manifest=self.backend.manifest(),
                   registry=self.registry,engineering=self.engineering)
        if result['status']=='SHADOW':
            card=FailureOperator.from_dict(result['card'])
            known={e['event_id']:e for e in self.store.visible(time.time(),self.run_id)}
            tid=known[payload['evidence_ids'][0]]['task_id']
            source=self.plan['source_rows'][tid]
            result['validation']=validate_and_publish(card,source,self.plan['gate_shards'][slot],
                root=folder/'environment_validation',data_root=self.plan['data_root'],registry=self.registry,
                runner=self.runner,client_factory=lambda label:self.client('validation-'+str(slot)+'-'+label),
                stream_id=self.run_id,experiment_id=self.plan['run_id'],after_sequence=payload['after_sequence'],
                engineering=self.engineering)
        self.events.append('LEARNING_DONE',dict(slot=slot,result=result),time.time())
        return result

    def resume_learning(self):
        rows=self.events.records()
        done={r['payload']['slot'] for r in rows if r['kind']=='LEARNING_DONE'}
        for row in rows:
            if row['kind']=='LEARNING_STARTED' and row['payload']['slot'] not in done:
                self._complete_learning(row['payload'])

    def run(self):
        self.health()
        self.ingest_history(Path(self.plan['source_run']))
        self.resume_learning()
        if not any(r['kind']=='LEARNING_STARTED' for r in self.events.records()):
            self.learn(0)
        completed={r['payload']['task_id']:r['payload'] for r in self.events.records() if r['kind']=='FUTURE_PAIRED_DONE'}
        for sequence,row in enumerate(self.plan['future_tasks'],1):
            if row['task_id'] in completed:
                record=next(r for r in self.events.records() if r['kind']=='FUTURE_PAIRED_DONE'
                            and r['payload']['task_id']==row['task_id'])
                self.after_pair(row,record)
                continue
            self.health()
            traces={}
            for arm in ('G','F'):
                path=self.root/'future'/row['task_id']/arm
                result_path=path/'result.json'
                if result_path.exists():
                    saved=read(result_path)
                    if saved['task_id']!=row['task_id'] or saved['sequence']!=sequence:
                        raise PermissionError('future checkpoint drift')
                    traces[arm]=saved
                    continue
                if (path/'STARTED.json').exists():
                    raise RunUnhealthy('interrupted environment episode requires audit; no replay of policy claims')
                save(path/'STARTED.json',dict(task_id=row['task_id'],sequence=sequence))
                client=self.client('future-'+arm)
                trace,initial=execute_episode(row,self.plan['data_root'],client,registry=self.registry,runner=self.runner,
                    stream_id=self.run_id,experiment_id=self.plan['run_id'] if arm=='F' else 'NO_PERMISSIONS',
                    sequence=sequence,events=self.events,engineering=self.engineering)
                self.health()
                verdict=dict(task_id=row['task_id'],sequence=sequence,status=classify_trace(trace),
                             trace=asdict(trace),initial_observation=initial)
                save(result_path,verdict)
                traces[arm]=verdict
            # Both answers are locked before the new F failure can enter learning.
            outcome=dict(task_id=row['task_id'],sequence=sequence,G=traces['G'],F=traces['F'],
                         gain=traces['F']['trace']['success'] and not traces['G']['trace']['success'],
                         regression=traces['G']['trace']['success'] and not traces['F']['trace']['success'])
            event=self.events.append('FUTURE_PAIRED_DONE',outcome,time.time())
            self.after_pair(row,event)
        self.report()

    def after_pair(self,row,event):
        if any(r['kind']=='AFTER_PAIR_DONE' and r['payload']['task_id']==row['task_id'] for r in self.events.records()):
            return
        outcome=event['payload']
        self.record_paired_use(event)
        sequence=outcome['sequence']
        if outcome['F']['status'] in ('STEP_LIMIT','ACTION_CYCLE','NO_PROGRESS'):
            path=self.root/'clients/future-F/requests.jsonl'
            requests={r['payload']['request_id'].removeprefix('future-F/'):r['payload'] for r in EvidenceStore(path).records()
                      if r['kind']=='ACTION_RESPONSE'}
            selections=[r['payload'] for r in self.events.records()
                        if r['kind']=='ENVIRONMENT_ACTION_SELECTED']
            import_episode(self.store,self.views,stream_id=self.run_id,row=row,event=event,
                requests=requests,initial_observation=outcome['F']['initial_observation'],
                available_from=time.time(),policy_selections=selections)
            if (sequence<len(self.plan['future_tasks']) and
                    not any(r['kind']=='LEARNING_STARTED' and r['payload']['after_sequence']==sequence
                            for r in self.events.records())):
                self.learn(sequence)
        self.events.append('AFTER_PAIR_DONE',dict(task_id=row['task_id'],sequence=sequence),time.time())

    def record_paired_use(self,event):
        outcome=event['payload']
        versions=outcome['F']['trace']['used_skills']
        cards={r['payload']['card']['version']:FailureOperator.from_dict(r['payload']['card'])
               for r in self.registry.events.records() if r['kind']=='SHADOW_REGISTERED'}
        for version in versions:
            if version not in cards:
                raise PermissionError('unknown executed policy version')
            receipt=dict(task_id=outcome['task_id'],candidate_version=version,
                         paired_record_hash=event['record_hash'],G_won=outcome['G']['trace']['success'],
                         F_won=outcome['F']['trace']['success'],
                         G_model_calls=outcome['G']['trace']['llm_call_count'],
                         F_model_calls=outcome['F']['trace']['llm_call_count'])
            prior=[r['payload'] for r in self.events.records() if r['kind']=='ALFWORLD_REUSE_OUTCOME'
                   and r['payload']['task_id']==outcome['task_id'] and r['payload']['candidate_version']==version]
            if prior and prior!=[receipt]:
                raise PermissionError('paired reuse receipt differs')
            if not prior:
                self.events.append('ALFWORLD_REUSE_OUTCOME',receipt,time.time())
            card=cards[version]
            if outcome['regression'] and self.registry.state(card)['permission']=='experimental':
                self.registry.suspend(card,'paired_future_reliability_regression',time.time())

    def report(self):
        rows=self.events.records()
        paired=[r['payload'] for r in rows if r['kind']=='FUTURE_PAIRED_DONE']
        registry=self.registry.events.records()
        summary=dict(scope='ENGINEERING_ONLY' if self.engineering else 'ALFWORLD_FAILURE_LEARNING_PILOT',
            trusted_failures=len(self.store.visible(time.time(),self.run_id)),
            learning_jobs=sum(r['kind']=='LEARNING_STARTED' for r in rows),
            registered=sum(r['kind']=='SHADOW_REGISTERED' for r in registry),
            authorized=sum(r['kind']=='EXPERIMENT_AUTHORIZED' for r in registry),
            future_tasks=len(paired),G_success=sum(p['G']['trace']['success'] for p in paired),
            F_success=sum(p['F']['trace']['success'] for p in paired),
            gains=sum(p['gain'] for p in paired),regressions=sum(p['regression'] for p in paired),
            future_operator_actions=sum(p['F']['trace']['direct_use_count'] for p in paired),
            future_intervened_tasks=sum(bool(p['F']['trace']['direct_use_count']) for p in paired),
            gains_with_intervention=sum(bool(p['gain'] and p['F']['trace']['direct_use_count']) for p in paired),
            gains_without_intervention=sum(bool(p['gain'] and not p['F']['trace']['direct_use_count']) for p in paired),
            budgets=dict(actions=self.actions.snapshot(),worker=self.tools.snapshot(),
                         learning=[b.snapshot() for b in self.job_budgets]))
        save(self.root/'learning_summary.json',summary)
        return summary
