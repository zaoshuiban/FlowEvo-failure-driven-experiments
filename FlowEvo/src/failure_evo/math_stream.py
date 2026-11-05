"""Default-off chronological G/T/F/R orchestration on existing controllers/ledgers.
No mathematical algorithm, scorer answer, or admission shortcut in this module.
"""
import copy,fcntl,json,os,time,hashlib
from dataclasses import asdict
from pathlib import Path
from .contracts import canonical,fingerprint
from .evidence import EvidenceStore
from .persistent_budget import PersistentBudget
from .run_health import assert_run_healthy,RunUnhealthy
from .math_transport import NoGoldSolverChannel
from .workflow_protocol_v2 import prepare,Limits
from .operator_version_gate import VersionGate
from .math_router import UnifiedMathRouter,MathQuality
from .semantic_contract import SplitRunner
from code_math.no_gold import PublicMathTask,NoGoldPolicy,NoGoldMathController
from code_math.private_math_scoring import PrivateMathScorer
VERSION='math-continuous-stream-v1'
ARMS=('G','T','F','R')

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(canonical(value)+'\n')
    with tmp.open('rb') as f:os.fsync(f.fileno())
    os.replace(tmp,path)

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def budget(path,run,ph,*,calls,tools=0):
    # Same maximum price on all tokens is a conservative reservation, not actual cost.
    return PersistentBudget(path,run_id=run,protocol_hash=ph,max_calls=calls,
        max_tokens=calls*73728,max_tools=tools,max_cost_microusd=calls*88474,
        token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,
        max_tool_milliseconds=tools*15000,tool_milliseconds_upper=15000,wall_seconds=7*86400)

class DurableSolver:
    """Recover only a fully received, usage-settled request; never resend consumed IDs."""
    durable_replay=True
    def __init__(self,path,b,*,engineering=False,sender=None,health=lambda:None,network_policy=None):
        self.budget=b;self.health=health;self.path=Path(path)
        self.cache=EvidenceStore(self.path/'response_cache.jsonl')
        cfg=b.config
        auth=dict(run_id=cfg['run_id'],protocol_hash=cfg['protocol_hash'],model='deepseek-flash',
            max_cost_microusd=cfg['max_cost_microusd'],paid_api_authorized=True,channel='math-solver-no-gold-v1')
        self.channel=NoGoldSolverChannel(b,self.path/'requests.jsonl',authorization=auth,mock=engineering,sender=sender,network_policy=network_policy)
    def generate_no_gold(self,*,messages,policy,request_id):
        self.health()
        prepared=prepare(messages,limits=Limits(input_token_upper=policy.input_upper,output_tokens=policy.output_tokens),temperature=policy.temperature)
        cached=[r['payload'] for r in self.cache.records() if r['payload']['request_id']==request_id]
        if cached:
            if len(cached)!=1 or cached[0]['wire_sha256']!=prepared.sha256:raise PermissionError('replay wire drift')
            return cached[0]['response']
        old=[r for r in self.channel.events.records() if r['payload'].get('request_id')==request_id]
        if old and self.budget.safe_pre_send(self.budget.request_state(request_id),self.channel.network_policy):
            response=self.channel.generate_no_gold(messages=messages,policy=policy,request_id=request_id)
        elif old:
            req=[r['payload'] for r in old if r['kind']=='NO_GOLD_REQUEST']
            raw=[r['payload']['response'] for r in old if r['kind']=='RAW_RESPONSE']
            done=[r['payload'] for r in old if r['kind']=='REQUEST_FINISHED']
            if len(req)!=1 or req[0]['wire_sha256']!=prepared.sha256 or len(raw)!=1 or not done or not any(x['status']=='COMPLETED' for x in done[-1]['audit']):
                raise RunUnhealthy('consumed request without settled response; no resend')
            # Global health above validates any explicitly isolated older request.
            # Recovery still requires THIS exact response to have settled usage.
            if self.budget.request_state(request_id)['status']!='settled':raise RunUnhealthy('response usage is not settled')
            r=raw[0];c=r['choices'][0]
            response=dict(text=c['message']['content'],usage=r['usage'],model=r['model'],finish_reason=c['finish_reason'],
                reasoning_tokens=r['usage'].get('completion_tokens_details',{}).get('reasoning_tokens',0),gold_exposed=False,
                origin='MOCK' if self.channel.mock else 'DEEPSEEK',request_sha256=prepared.sha256)
        else:response=self.channel.generate_no_gold(messages=messages,policy=policy,request_id=request_id)
        self.cache.append('REPLAYABLE_RESPONSE',dict(request_id=request_id,wire_sha256=prepared.sha256,response=response),time.time())
        return response

class PublicProblemProbe:
    """Adapter for the existing GPT-produced match(problem) contract, no host matcher.
    Not a claim of typed semantic parsing. Unknown premises still refuse via SplitRunner.
    """
    allow_mock=False
    def __init__(self,split,*,engineering=False):
        self.split=split;self.allow_mock=engineering;self.usage={}
        self.sha256=fingerprint(dict(protocol='existing-public-match-probe-v1',semantic_source=sha(Path(__file__).with_name('semantic_contract.py'))))
    def prepare(self,task):
        if not isinstance(task,PublicMathTask):raise TypeError('public task')
        self.usage={};return task.problem
    def match(self,a,problem):return self.split.match(a,problem)

class StreamRuntime:
    def __init__(self,path,plan,tasks,private_rows,lineage,*,backend,learner_factory,
                 engineering=False,sender_factory=None,fault=None,budget_factory=None):
        self._active_contract_publications=set()
        self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
        self.plan=copy.deepcopy(plan);self.tasks=[PublicMathTask.parse(t) for t in tasks]
        self.lineage=copy.deepcopy(lineage);self.engineering=engineering;self.fault=fault or (lambda *a:None)
        if plan.get('network_policy'):
            from .network_transport import validate_policy
            validate_policy(plan['network_policy'])
        if len({t.task_id for t in self.tasks})!=len(self.tasks):raise ValueError('duplicate task')
        if plan['tasks_sha256']!=fingerprint(tasks) or set(lineage)!={t.task_id for t in self.tasks}:raise ValueError('manifest binding')
        expected_credit=plan.get('auxiliary_calls_per_window',3+4*plan['max_gate_cases'])
        if type(expected_credit) is not int or expected_credit<3+4*plan['max_gate_cases'] or plan['window']<1 or plan['r_policy'] not in ('previous-window-f-call-credit-v1','previous-completed-window-f-call-credit-v2') or plan['r_max_extra_calls']!=expected_credit:raise ValueError('frozen window / retry protocol')
        if 'auxiliary_calls_per_window' in plan and 'cumulative' not in plan:raise ValueError('separate cumulative credit protocol required')
        self.ph=fingerprint(plan);self.events=EvidenceStore(self.path/'stream.jsonl');self.arms={}
        make_budget=budget_factory or budget
        prior=self.events.records()
        if prior:
            if prior[0]['kind']!='STREAM_FROZEN' or prior[0]['payload']!=plan:raise PermissionError('plan drift')
        else:self.events.append('STREAM_FROZEN',plan,time.time())
        rows={r['task_id']:r for r in private_rows}
        if set(rows)!={t.task_id for t in self.tasks}:raise ValueError('private task set')
        for t in self.tasks:
            if rows[t.task_id]['problem_sha256']!=fingerprint(t.problem):raise ValueError('private hash')
        for arm in ARMS:
            d=self.path/arm;reg=VersionGate(d/'registry.jsonl');self.arms[arm]=dict(path=d,registry=reg)
            windows=(len(tasks)-1)//plan['window'];extra=plan['r_max_extra_calls']*windows if arm=='R' else 0
            b=make_budget(d/'solve_budget.jsonl',('engineering:' if engineering else '')+self.path.name+':'+arm+':solve',self.ph,calls=2*len(tasks)+extra)
            tool=make_budget(d/'tool_budget.jsonl',('engineering:' if engineering else '')+self.path.name+':'+arm+':tools',self.ph,calls=0,tools=plan['max_tools_per_arm'])
            client=DurableSolver(d,b,engineering=engineering,sender=sender_factory(arm) if sender_factory else None,health=self.health,network_policy=plan.get('network_policy'))
            split=SplitRunner(backend,d/'worker.jsonl',tool);probe=PublicProblemProbe(split,engineering=engineering)
            router=UnifiedMathRouter(reg,probe,engineering=engineering) if arm in ('T','F') else None
            if router:
                existing=router.quality.feedback_role(self.tasks[0].task_id)
                if existing is None:router.quality.freeze_feedback_roles({t.task_id:'ONLINE_POST_TASK' for t in self.tasks})
            self.arms[arm].update(budget=b,tool_budget=tool,client=client,split=split,probe=probe,router=router,
                states=EvidenceStore(d/'task_state.jsonl'),controller=EvidenceStore(d/'controller.jsonl'),
                scorer=PrivateMathScorer(private_rows,d/'controller.jsonl',d/'scores.jsonl',strict_delivery=True))
            if plan.get('operator_contract_shadow'):
                if plan['operator_contract_shadow']!='pre-score-one-candidate-v1':raise PermissionError('unknown Shadow policy')
                from .math_contract_runtime import ContractShadow
                self.arms[arm]['contract_shadow']=ContractShadow(self,arm,private_rows) if arm in ('T','F') else None
            self.arms[arm]['learner']=learner_factory(self,arm) if arm in ('T','F') else None
    def health(self):
        if fingerprint(self.plan)!=self.ph:raise RunUnhealthy('in-memory protocol drift')
        root=Path(__file__).resolve().parents[3]
        for rel,digest in self.plan.get('sources',{}).items():
            if sha(root/rel)!=digest:raise RunUnhealthy('frozen implementation changed: '+rel)
        isolated=set()
        if self.plan.get('continuation_binding'):
            from .math_continuation import verify
            m=verify(self.path,self.plan)
            isolated={(q['ledger'],q['request_id']) for q in m['isolations']}
        for arm in self.arms.values():
            rows=arm['registry'].events.records()
            completed={r['payload'].get('execution_id') for r in rows if r['kind']=='OPERATOR_VALIDATOR_EXECUTED'}
            shadow_done={r['payload'].get('execution_id') for r in rows if r['kind']=='CONTRACT_SHADOW_EXECUTED'}
            publication_done={r['payload'].get('version') for r in rows if r['kind']=='CONTRACT_RELEASE_RESUME_DONE'}
            if any(r['kind']=='CONTRACT_RELEASE_RESUME_STARTED' and r['payload'].get('version') not in publication_done and r['payload'].get('version') not in getattr(self,'_active_contract_publications',set()) for r in rows):raise RunUnhealthy('unresolved publication; audit required')
            if any(r['kind']=='OPERATOR_VALIDATOR_STARTED' and r['payload'].get('execution_id') not in completed for r in rows):raise RunUnhealthy('unresolved validator execution; audit required')
            if any(r['kind']=='CONTRACT_SHADOW_STARTED' and r['payload'].get('execution_id') not in shadow_done for r in rows):raise RunUnhealthy('unresolved Shadow execution; audit required')
        # Check ALL account journals, including learner accounts restored after process restart.
        for p in self.path.rglob('*budget.jsonl'):
            b=PersistentBudget.__new__(PersistentBudget);b.path=p
            with b._locked() as rows:
                states,_=b._state(rows)
                if any(x['status'] not in ('settled','not_sent') and not b.safe_pre_send(x,self.plan.get('network_policy'))
                       and (str(p.relative_to(self.path)),rid) not in isolated for rid,x in states.items()):raise RunUnhealthy('unresolved ledger '+str(p))
        for p in self.path.rglob('provider.jsonl'):
            rows=EvidenceStore(p).records();start={r['payload']['key'] for r in rows if r['kind']=='SEND_STARTED'};received={r['payload']['key'] for r in rows if r['kind']=='RAW_RESPONSE'}
            if start-received or any(r['kind']=='SEND_UNKNOWN' for r in rows):raise RunUnhealthy('unresolved provider '+str(p))
    def emit_once(self,store,kind,key,payload):
        old=[r['payload'] for r in store.records() if r['kind']==kind and r['payload'].get('id')==key]
        value=dict(id=key,**payload)
        if old:
            if old!=[value]:raise PermissionError('conflicting checkpoint '+kind)
        else:store.append(kind,value,time.time())
    def solve(self,arm,task,seq):
        a=self.arms[arm];eid=f'{arm}/{seq}/{task.task_id}'
        done=[r['payload']['lock'] for r in a['states'].records() if r['kind']=='ANSWER_LOCKED' and r['payload']['id']==eid]
        if done:return done[0]
        self.emit_once(a['states'],'TASK_STARTED',eid,dict(task_id=task.task_id,sequence=seq))
        policy=NoGoldPolicy(delivery_profile='concise-v1',operators_enabled=arm in ('T','F'))
        ctl=NoGoldMathController(a['client'],a['controller'].path,policy=policy,library=a['router'])
        lock=ctl.solve(task,episode_id=eid+'/base',sequence=seq,resume=True)
        allowance=0
        retry_boundary=(seq%self.plan['window']==0 if self.plan['r_policy']=='previous-window-f-call-credit-v1' else (seq-1)%self.plan['window']==0)
        if arm=='R' and retry_boundary and seq>self.plan['window']:
            previous=seq-self.plan['window'] if self.plan['r_policy']=='previous-window-f-call-credit-v1' else seq-1;window=self.arms['F']['path']/'learning'/str(previous)
            if not (window/'result.json').exists():raise RunUnhealthy('preceding F window not complete')
            for ledger in window.rglob('*budget.jsonl'):
                b=PersistentBudget.__new__(PersistentBudget);b.path=ledger
                with b._locked() as rows:
                    states,_=b._state(rows)
                    allowance+=sum(v['kind']=='model' and v['status']!='not_sent' for v in states.values())
            if allowance>self.plan['r_max_extra_calls']:raise PermissionError('R credit exceeds frozen bound')
            self.emit_once(a['states'],'RETRY_CREDIT',eid,dict(previous_window=previous,extra_calls=allowance,selection='last_scheduled_response',source='past F call counts only; no content or grades'))
        if allowance:
            # One-window-lagged past compute only. No current score or F content is exposed.
            parts=[lock]
            counts=[2]*(allowance//2)+([1] if allowance%2 else [])
            for j,n in enumerate(counts):
                extra=NoGoldMathController(a['client'],a['controller'].path,
                    policy=NoGoldPolicy(delivery_profile='concise-v1',reflection_calls=n-1,input_upper=65536,output_tokens=8192))
                parts.append(extra.solve(task,episode_id=eid+'/extra'+str(j),sequence=seq,resume=True))
            allr=[r for p in parts for r in p['responses']]
            lock=dict(parts[-1],episode_id=eid+'/final',responses=allr,selection='last_preregistered_restart_no_score_selection',
                model_calls=sum(p['model_calls'] for p in parts),input_tokens=sum(p['input_tokens'] for p in parts),
                output_tokens=sum(p['output_tokens'] for p in parts),reasoning_tokens=sum(p['reasoning_tokens'] for p in parts),
                seconds=sum(p['seconds'] for p in parts))
            lock.pop('locked_sha256');lock['locked_sha256']=fingerprint(lock)
            existing=[r['payload'] for r in a['controller'].records() if r['kind']=='MATH_ANSWER_LOCKED' and r['payload']['episode_id']==eid+'/final']
            if existing:
                if existing!=[lock]:raise PermissionError('R final lock drift')
            else:a['controller'].append('MATH_ANSWER_LOCKED',lock,time.time())
        self.fault('after_answer_lock',arm,seq)
        self.emit_once(a['states'],'ANSWER_LOCKED',eid,dict(task_id=task.task_id,sequence=seq,lock=lock))
        return lock
    def evidence(self,arm,cutoff):
        a=self.arms[arm];out=[]
        tasks={t.task_id:t for t in self.tasks}
        locks={r['payload']['id']:r['payload']['lock'] for r in a['states'].records() if r['kind']=='ANSWER_LOCKED'}
        for r in a['states'].records():
            if r['kind']!='PRIVATE_SCORED' or r['payload']['sequence']>cutoff:continue
            p=r['payload'];g=p['verdict'];l=locks[p['id']]
            if g['status']!='CONFIRMED_WRONG':continue
            if not l['responses'] or l['responses'][-1]['finish_reason']!='stop':continue
            out.append(dict(event_id=fingerprint([p['id'],g['locked_sha256']]),sequence=p['sequence'],task=tasks[p['task_id']].to_dict(),
                correct=False,final_output=l['final_output'],trajectory=l['responses'],locked_sha256=l['locked_sha256']))
        return out
    def source_review(self,arm,task,result,cutoff):
        """Host-only diagnostic, never passed to compiler; no expected answer returned."""
        state=self.arms[arm]
        if not any(r['kind']=='PRIVATE_SCORED' and r['payload']['task_id']==task.task_id and r['payload']['sequence']<=cutoff for r in state['states'].records()):
            raise PermissionError('source review precedes task lock/score')
        if result['status']!='APPLIED':return dict(status=result['status'],correct=None)
        from code_math.discovery_continuation import grade_continuation
        g=grade_continuation(result['answer'],state['scorer']._rows[task.task_id]['gold_answer'],'stop')
        return dict(status=g['status'],correct=g['correct'])
    def history_packet(self,arm,cutoff):
        # Shared selection based only on public order/length, never on F outcomes.
        window=self.tasks[max(0,cutoff-self.plan['window']):cutoff];chosen=[];size=0
        for t in reversed(window):
            n=len(t.problem.encode())
            if len(chosen)<6 and size+n<=16000:chosen.append(t);size+=n
        chosen.reverse();packet=dict(questions=[dict(problem=t.problem) for t in chosen])
        refs=dict(task_ids=[t.task_id for t in chosen],cutoff_sequence=cutoff,
                  omitted_task_ids=[t.task_id for t in window if t not in chosen])
        if arm=='F':
            errors={e['task']['task_id']:e for e in self.evidence(arm,cutoff)}
            packet['observations']=[]
            for t in chosen:
                if t.task_id not in errors:continue
                e=errors[t.task_id];packet['observations'].append(dict(problem=t.problem,correct=False,
                    final_output=dict(text=e['final_output'][:1500],is_fragment=len(e['final_output'])>1500,sha256=fingerprint(e['final_output'])),
                    trajectory=[dict(text=r['text'][:1000],is_fragment=len(r['text'])>1000,sha256=fingerprint(r['text']),finish_reason=r['finish_reason']) for r in e['trajectory']]))
        return packet,refs
    def run(self,*,stop_after_window=None):
        # Prevent two host processes consuming the same persistent state.
        with (self.path/'stream.lock').open('a') as f:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.health()
            for seq,task in enumerate(self.tasks,1):
                locks={}
                order=ARMS[(seq-1)%4:]+ARMS[:(seq-1)%4]
                for arm in order:
                    self.health()
                    if self.arms[arm].get('contract_shadow'):self.arms[arm]['contract_shadow'].observe(task,seq)
                    locks[arm]=self.solve(arm,task,seq)
                # Barrier: every arm's final answer is durable before ANY private score.
                for arm in ARMS:
                    a=self.arms[arm];eid=f'{arm}/{seq}/{task.task_id}'
                    v=a['scorer'].score(task,locks[arm])
                    self.emit_once(a['states'],'PRIVATE_SCORED',eid,dict(task_id=task.task_id,sequence=seq,verdict=v))
                    if a.get('contract_shadow'):a['contract_shadow'].finalize(task,locks[arm])
                    original=self.lineage[task.task_id]['source_original_id']
                    if a['router'] and any(r['kind']=='MATH_ROUTER_EXECUTED' and r['payload']['task_id']==task.task_id for r in a['registry'].events.records()):
                        if original=='UNKNOWN':raise PermissionError('cannot record unknown original as verified reuse')
                        a['router'].record_feedback(task,locks[arm],v,controller=a['controller'],scorer=a['scorer'].events,original_id=original)
                if self.plan.get('operator_contract_shadow'):
                    for arm in ('T','F'):
                        self.arms[arm]['learner'].release.poll_contract(seq)
                self.fault('after_scoring',None,seq)
                if seq%self.plan['window']==0 or seq==len(self.tasks):
                    for arm in ('T','F'):
                        if seq<len(self.tasks):self.arms[arm]['learner'].learn(seq)
                    for arm in ARMS:
                        a=self.arms[arm];self.emit_once(a['states'],'WINDOW_COMPLETED',str(seq),dict(cutoff_sequence=seq))
                    self.emit_once(self.events,'WINDOW_COMPLETED',str(seq),dict(cutoff_sequence=seq))
                    save(self.path/'progress.json',dict(completed_tasks=seq,total_tasks=len(self.tasks),status='COMPLETE' if seq==len(self.tasks) else 'RUNNING'))
                    if stop_after_window is not None and seq//self.plan['window']>=stop_after_window:return
            self.emit_once(self.events,'STREAM_COMPLETED','complete',dict(tasks=len(self.tasks),paid_api=not self.engineering))
