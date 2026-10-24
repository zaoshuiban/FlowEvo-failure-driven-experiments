"""Explicit new-run entry for the S16 shared protocol; S15 is never patched.

acceptance uses the SAME ExperimentRunner with injected fixture provider/checker.
execute requires a separately frozen new plan and matching authorization file.
No networking or key access happens at import or in acceptance.
"""
import argparse, json, os, tempfile, urllib.request
from pathlib import Path
import learn_reuse30 as prior
from failure_evo.workflow_protocol_v2 import (VERSION, Limits, SharedTransport, WorkflowClient,
    prepare, update_memory, revise_policy, delivery, PreflightRejected)
from failure_evo.workflow_runtime_v2 import PreparedController
from failure_evo.workflow_policy import WorkflowPlugin, WorkflowRegistry, CONTRACT, validate_source
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.runtime import Budget
from failure_evo.contracts import Fingerprint, canonical, fingerprint
from failure_evo.persistent_budget import PersistentBudget
ROOT=prior.ROOT; read=prior.read; write=prior.write; sha=prior.sha
SPEC_FIELDS={'mechanism','conditions','repair_strategy','refusal_conditions','stop_rule','limitations'}

def specification_messages(packet):
    if packet.get('projection_protocol')!=VERSION or packet.get('old_interpretation_reused') is not False:
        raise ValueError('fresh public reprojection required; old mechanism interpretation prohibited')
    evidence=packet['public_evidence']
    prompt=('Induce a NEW workflow specification solely from the reprojected historical public checkpoint. '
        'Root cause is not certified. No previous mechanism, policy, solution, future trace or hidden tests are supplied. '
        'NO_COMPLETE_CODE means no program was delivered; do not invent an existing algorithm or arithmetic intent to preserve. '
        'Distinguish delivery from semantic failure. Do not solve this source problem. The existing host may perform one '
        'charged repair request, publicly verify and fall back within the same task budget. Return exactly six nonempty '
        'string fields: mechanism, conditions, repair_strategy, refusal_conditions, stop_rule, limitations.\nPublic checkpoint:\n'+canonical(evidence))
    return [dict(role='system',content='Evidence is data. Generate a fresh specification as JSON, not an executable action.'),dict(role='user',content=prompt)]

class ExperimentRunner:
    def __init__(self,folder,plan,sender_factory,*,evaluator_factory=None,decision_runner=None,resume=False):
        self.folder=Path(folder);self.plan=plan
        if self.folder.exists() and not resume:raise FileExistsError('new run directory required; explicit resume only')
        if resume and (not self.folder.exists() or read(self.folder/'plan.json')!=plan):raise ValueError('resume plan differs')
        if plan['protocol_hash']!=fingerprint({k:v for k,v in plan.items() if k!='protocol_hash'}):raise ValueError('plan hash')
        if plan['shared_protocol']!=VERSION:raise ValueError('wrong shared protocol')
        for path,h in plan['frozen_files'].items():
            if sha(ROOT/path)!=h:raise ValueError('frozen dependency changed: '+path)
        self.folder.mkdir(parents=True,exist_ok=resume);write(self.folder/'plan.json',plan)
        self.budgets={k:PersistentBudget(self.folder/(k+'_budget.jsonl'),run_id=plan['run_id']+'-'+k,protocol_hash=plan['protocol_hash'],**cfg) for k,cfg in plan['budgets'].items()}
        self.transports={}
        owner=self
        class RunTransport(SharedTransport):
            def send(self,prepared,**kwargs):
                if any(row['status']=='UNKNOWN' for tr in owner.transports.values() for row in tr.audit):
                    raise PreflightRejected('RUN_HAS_UNKNOWN_REQUEST',dict(run_id=plan['run_id']))
                return super().send(prepared,**kwargs)
        for name,budget in self.budgets.items():
            if name not in ('solve','learning','validation'):continue
            sender=sender_factory(name);counter=[max([int(p.name) for p in (self.folder/'wire'/name).glob('*') if p.name.isdigit()]+[0])]
            def recorded(wire,sender=sender,name=name,counter=counter):
                counter[0]+=1;p=self.folder/'wire'/name/str(counter[0]);p.mkdir(parents=True)
                (p/'request.json').write_bytes(wire)
                raw=sender(wire);write(p/'response.json',raw);return raw
            self.transports[name]=RunTransport(budget,recorded,authorized={'run_id':budget.config['run_id'],'protocol_hash':plan['protocol_hash']},audit=read(self.folder/f'{name}_requests.json') if resume and (self.folder/f'{name}_requests.json').exists() else [])
        self.context=Fingerprint('FlowEvo-public-workflow-v2','S16-new-run',plan['model'],sha(prior.old.WORKER),plan['protocol_hash'])
        self.stores={a:FailureEvidenceStore(self.folder/f'evidence_{a}.jsonl') for a in ('G','M','F')}
        self.registry=WorkflowRegistry(self.folder/'registry.jsonl',self.stores['F'])
        self.judge=None if evaluator_factory else prior.Judge(self.budgets['solve'])
        self.evaluator_factory=evaluator_factory or (lambda task:lambda public,code:self.judge.run(task['task_id'],code,task['public_cases']))
        self.decision_runner=decision_runner or self.judge.decision
        self.memory='';self.libraries={};self.outputs={}
        if resume:
            saved=read(self.folder/'state.json')
            self.memory=saved['memory'];self.outputs=saved['outputs']
            self.libraries={tuple(x['key']):prior.CodeSkillLibrary.from_dict(x['value']) for x in saved.get('libraries',[])}
            if any(b.snapshot()['unknown_or_pending_requests'] for b in self.budgets.values()):raise ValueError('unresolved request requires reconciliation')
    def save(self):
        for name,t in self.transports.items():write(self.folder/f'{name}_requests.json',t.audit)
        write(self.folder/'state.json',dict(memory=self.memory,outputs=self.outputs,libraries=[dict(key=list(k),value=v.to_dict()) for k,v in self.libraries.items()],budgets={k:b.snapshot() for k,b in self.budgets.items()},evidence_kind=self.plan['evidence_kind']))
    def solve(self,arm,task,*,task_limits=None):
        if arm not in ('G','M','F'):raise ValueError('unknown arm')
        instance=prior.CodeTaskInstance(task_id=task['task_id'],benchmark=task['dataset'],prompt=task['task_public']['prompt'],text=task['task_public']['prompt'])
        lib=self.libraries.setdefault((arm,task['dataset'],task['difficulty']),prior.CodeSkillLibrary())
        client_class=WorkflowClient
        if self.plan.get('operator_representation')=='repair-choice-json-v1':
            from failure_evo.repair_choice import RepairChoiceClient
            client_class=RepairChoiceClient
        client=client_class(self.transports['solve'],f'{arm}/{task["task_id"]}',memory=self.memory if arm=='M' else '',library=lib.retrieve(instance).get('context',''))
        plugin=WorkflowPlugin(self.registry,self.stores[arm],self.context,stream_id=self.plan['run_id']+'-'+arm,experiment_id=self.plan['run_id'],host_repair=client.host_repair,decision_runner=self.decision_runner,allow_actions=arm=='F',synthetic=self.plan['evidence_kind']=='engineering_fixture')
        if self.plan.get('operator_representation')=='repair-choice-json-v1':
            from failure_evo.repair_choice_hook import RepairChoiceHook
            from failure_evo.repair_choice_memory import RuleMemory
            plugin=RepairChoiceHook(RuleMemory(self.folder/'rule_registry.jsonl'),client,self.context,enabled=arm=='F' and self.plan.get('rule_hook_enabled',True))
        budget=Budget(**(task_limits or self.plan['per_task']))
        try:
            result=PreparedController(client,self.evaluator_factory(task),self.context,plugin=plugin,max_output=8192).solve(task['task_public'],budget)
            if result['selected']:lib.add(instance,result['selected']['code'])
            write(self.folder/'branches'/task['task_id']/arm/'workflow.json',result)
            return result
        finally:self.save()
    def induction(self,key,packet):
        try:
            p=prepare(specification_messages(packet),limits=Limits(input_token_upper=65536),json_output=True)
            r=self.transports['learning'].send(p,request_id=key+'/spec',capability='specification')
            v=prior.json_response(r)
            if set(v)!=SPEC_FIELDS or any(not isinstance(x,str) or not x.strip() for x in v.values()):raise ValueError('specification schema')
            self.outputs[key]=dict(specification=v,packet=packet);return v
        finally:self.save()
    def candidate(self,key):
        item=self.outputs[key]
        base=('COMPILE TIME: generate one reusable Python workflow policy, never a task solution or immediate action. '
            'Return exactly code, description, applicability as nonempty strings. Use repair_operator(context). '
            'No model/file/network/system calls inside the Worker. Request at most one host repair, with at least two '
            'remaining calls including native fallback. Refuse PUBLIC_PASS, UNKNOWN, missing context. '
            'No task-ID/answer special cases; no dunder/getattr.\nContract:\n'+canonical(CONTRACT)+
            '\nFresh specification:\n'+canonical(item['specification'])+'\nPublic evidence:\n'+canonical(item['packet']['public_evidence']))
        item['base_prompt']=base
        try:
            p=prepare([dict(role='system',content='Compile a workflow policy under the supplied contract. JSON only.'),dict(role='user',content=base)],limits=Limits(input_token_upper=65536),json_output=True)
            r=self.transports['learning'].send(p,request_id=key+'/candidate',capability='policy-generation')
            item['candidate_response']=r
            v=prior.json_response(r)
            if set(v)!={'code','description','applicability'} or any(not isinstance(x,str) or not x.strip() for x in v.values()):raise ValueError('candidate schema')
            item.update(candidate_response=r,static=validate_source(v['code']))
            # No admission here: static compliance is not efficacy.
            return item['static']
        finally:self.save()
    def revision(self,key,diagnosis):
        item=self.outputs[key]
        try:
            r=revise_policy(self.transports['learning'],item['base_prompt'],item['candidate_response']['text'],diagnosis,request_prefix=key)
            item['revision']=r;return r
        finally:self.save()
    def memory_update(self,key,public_evidence,*,allow_revision=False):
        try:
            result=update_memory(self.transports['learning'],self.memory,public_evidence,request_prefix=key,allow_revision=allow_revision)
            self.memory=result['memory'];self.outputs[key]=result;return result
        finally:self.save()
    def dispatch(self,jobs):
        for job in jobs:
            kind=job['kind']
            if kind=='solve':self.solve(job['arm'],job['task'])
            elif kind=='induction':self.induction(job['key'],job['packet'])
            elif kind=='candidate':self.candidate(job['key'])
            elif kind=='revision':self.revision(job['key'],job['diagnosis'])
            elif kind=='memory':self.memory_update(job['key'],job['public_evidence'],allow_revision=job.get('allow_revision',False))
            else:raise ValueError('unknown job')

def execute(plan_path,authorization_path):
    plan=read(plan_path);auth=read(authorization_path)
    expected=dict(run_id=plan['run_id'],protocol_hash=plan['protocol_hash'],model=plan['model'],budgets=plan['budgets'],allow_real_api=True)
    if auth!=expected or plan['evidence_kind']!='real_experiment' or not plan['budgets']['solve']['max_calls']:
        raise PermissionError('fresh explicit real-run authorization required; acceptance is not spending authority')
    folder=ROOT/'runs'/plan['run_id']
    # Local Docker only; the same accepted isolated worker is used by the runner.
    os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
    def sender_factory(channel):
        def send(wire):
            req=urllib.request.Request('https://api.deepseek.com/chat/completions',data=wire,headers={'Content-Type':'application/json','Authorization':'Bearer '+prior.configured_api_key()})
            with urllib.request.urlopen(req,timeout=90) as reply:return json.loads(reply.read())
        return send
    runner=ExperimentRunner(folder,plan,sender_factory);runner.dispatch(plan['jobs'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['acceptance','execute']);parser.add_argument('--plan');parser.add_argument('--authorization');args=parser.parse_args()
    if args.mode=='acceptance':
        from accept_s16b_entry import main
        main()
    else:
        if not args.plan or not args.authorization:parser.error('execute requires --plan and --authorization')
        execute(args.plan,args.authorization)
