"""Failure-driven ALFWorld policies on the existing compiler, Worker and registry."""
import ast
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

from failure_evo.autonomous_generation import DeepSeekCompilerAdapter, HYPOTHESIS_SCHEMA, parse_hypothesis
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import Fingerprint, PublicFeedback, canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import ENVIRONMENT_HOOK, FailureOperator, FailureOperatorRegistry
from failure_evo.math_operators import validate_math_source
from failure_evo.math_skill_transfer import replay_train_generation
from failure_evo.math_stream import save
from failure_evo.run_health import RunUnhealthy

VERSION='alfworld-failure-policy-v1'
SOURCE_CONTRACT="""Generate a deterministic Python environmental policy from the unverified hypothesis.
Implement def environment_operator(context), one argument, without decorators or annotations.
context has exactly goal, observation, admissible_commands, history, state.
history contains public action/observation pairs from this episode; state is your bounded JSON memory.
Return exactly {'status':'applied','action': a command from admissible_commands,'state':{},'reason': explanation}
or {'status':'declined','state':{},'reason': explanation}.
Compute and choose a real environment action. A prompt asking another model to solve is not an action.
Declare preconditions, exclusions and bounded complexity in description/applicability strings.
No task IDs, game IDs, hidden state, expert plans, reference trajectories or expected commands are available.
Do not specialize to source instances. The model must propose the policy algorithm itself.
Allowed imports: json, math, collections, itertools, functools, re, heapq, bisect, fractions, statistics.
No filesystem, network, processes, reflection, dynamic execution, dunder access, model calls or permissions.
Only top-level imports, constant literals and ordinary functions. Do not run self-tests at import.
The host executes exact source in a restricted Linux Worker and checks action legality.
Return JSON with exactly three nonempty strings: code, description, applicability. No test or permission claims.
"""


class EnvironmentCompilerAdapter(DeepSeekCompilerAdapter):
    protocol=VERSION
    source_contract=SOURCE_CONTRACT

    def preflight(self,request):
        self._authorize()
        evidence=request['discovery']
        if (set(evidence)!={'evidence','shared_cause'} or evidence['shared_cause']!='UNVERIFIED'
                or not evidence['evidence']):
            raise PermissionError('environment discovery whitelist')
        for event in evidence['evidence']:
            if set(event)!={'evidence_id','goal','initial_observation','steps','won','trace_sha256','omitted_steps'} or event['won'] is not False:
                raise PermissionError('only confirmed public failure traces')
            for step in event['steps']:
                if set(step)!={'action','observation','decision_output','actor'}:
                    raise PermissionError('private or future trajectory material')
        induction=request['phase']=='induction'
        payload=dict(protocol=VERSION,public_failures=evidence['evidence'])
        if not induction:
            payload['hypothesis']=parse_hypothesis(json.loads(request['specification']))
            if payload['hypothesis']['decision']!='PROPOSE':
                raise PermissionError('no proposed mechanism')
        system=('Analyze only these past public failed episodes. Distinguish observations from uncertain causes. '
                'Propose your own reusable deterministic action policy if justified; otherwise NO_MECHANISM. '
                'Shared failure does not prove a common mechanism. No requested algorithm or task blueprint is provided. '
                'Return exactly this JSON schema: '+canonical(HYPOTHESIS_SCHEMA)) if induction else SOURCE_CONTRACT
        wire=dict(model=self.model,messages=[dict(role='system',content=system),
                  dict(role='user',content=canonical(payload))],max_tokens=request['max_tokens'],temperature=0,
                  thinking={'type':'disabled'},reasoning_effort='none',response_format={'type':'json_object'},stream=False)
        if len(canonical(wire).encode())+256>self.max_wire_input_upper:
            raise ValueError('EVIDENCE_REPRESENTATION_LIMIT')
        return wire


def static_check(code):
    if not isinstance(code,str) or len(code.encode())>65536:
        return dict(passed=False,errors=['SOURCE_BOUND'])
    try:
        tree=ast.parse(code)
    except SyntaxError:
        return dict(passed=False,errors=['SYNTAX'])
    entries=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='environment_operator']
    if len(entries)!=1:
        return dict(passed=False,errors=['ENTRY'])
    args=entries[0].args
    if len(args.args)!=1 or args.posonlyargs or args.vararg or args.kwarg or args.kwonlyargs:
        return dict(passed=False,errors=['SIGNATURE'])
    # Permission lint only. The adapter below is never written or executed.
    check=validate_math_source(code+"\ndef math_operator(context):\n return {'status':'DECLINED','reason':'permission-lint-only'}\n")
    return dict(passed=check['passed'],errors=check['errors'],source_sha256=hashlib.sha256(code.encode()).hexdigest())


def context_view(goal,observation,commands,history,state):
    value=dict(goal=goal,observation=observation,admissible_commands=list(commands),
               history=[dict(action=x['action'],observation=x['observation']) for x in history],state=state)
    if (not isinstance(goal,str) or not isinstance(observation,str)
            or not all(isinstance(c,str) for c in commands) or not isinstance(state,dict)
            or len(canonical(value).encode())>65536 or len(canonical(state).encode())>4096):
        raise ValueError('environment context bounds')
    return value


class EnvironmentPolicyRunner:
    def __init__(self,backend,journal,budget):
        if type(backend) is not FrozenLinuxBackend:
            raise TypeError('existing frozen Linux Worker required')
        self.backend,self.events,self.budget=backend,EvidenceStore(journal),budget

    def run(self,card,context):
        if card.operator_kind!='environment_policy' or not card.intact():
            raise PermissionError('changed or non-environment artifact')
        check=static_check(Path(card.artifact_path).read_text())
        if not check['passed']:
            raise PermissionError('policy safety rejection')
        identity=fingerprint([card.version,context,self.backend.manifest()])
        rows=self.events.records()
        done=[r['payload'] for r in rows if r['kind']=='ENVIRONMENT_POLICY_EXECUTED'
              and r['payload'].get('execution_id')==identity]
        if done:
            return done[-1]['result']
        if any(r['kind']=='ENVIRONMENT_POLICY_STARTED' and r['payload']['execution_id']==identity for r in rows):
            raise RunUnhealthy('interrupted policy execution requires audit')
        self.events.append('ENVIRONMENT_POLICY_STARTED',dict(execution_id=identity),time.time())
        started=time.monotonic()
        key=self.budget.tool(capability='environment-policy',request_hash=fingerprint([card.version,context]))
        try:
            with self.backend(card.artifact_path) as worker:
                raw=worker.call(dict(mode='function',function='environment_operator',args=[context],timeout=2))
        finally:
            self.budget.settle(key,tool_milliseconds=int((time.monotonic()-started)*1000))
        if raw['status'] in ('EVALUATOR_ERROR','WORKER_ERROR'):
            raise RunUnhealthy('environment policy Worker fault')
        result=raw.get('value')
        reason=None
        if (raw['status']!='OK' or not isinstance(result,dict) or result.get('status') not in ('applied','declined')
                or set(result)!=({'status','action','state','reason'} if result.get('status')=='applied' else {'status','state','reason'})
                or not isinstance(result.get('reason'),str) or not isinstance(result.get('state'),dict)
                or len(canonical(result).encode())>8192 or len(canonical(result.get('state',{})).encode())>4096):
            reason='OUTPUT_CONTRACT'
        elif result['status']=='applied' and result['action'] not in context['admissible_commands']:
            reason='ACTION_NOT_ADMISSIBLE'
        if reason:
            result=dict(status='error',state={},reason=reason)
        receipt=dict(execution_id=identity,candidate_version=card.version,artifact_sha256=card.artifact_sha256,
                     context_sha256=fingerprint(context),raw=raw,result=result,
                     seconds=time.monotonic()-started,worker_sha256=fingerprint(self.backend.manifest()))
        self.events.append('ENVIRONMENT_POLICY_EXECUTED',receipt,time.time())
        return result


def import_episode(store,views,*,stream_id,row,event,requests,initial_observation,available_from,policy_selections=()):
    """Trusted host supplies an actually locked complete episode and matching raw responses."""
    if event['kind']=='EPISODE_LOCKED':
        episode=event['payload']
    elif event['kind']=='FUTURE_PAIRED_DONE':
        episode=event['payload']['F']
    else:
        return None
    if (episode['status'] not in ('STEP_LIMIT','ACTION_CYCLE','NO_PROGRESS')
            or episode['task_id']!=row['task_id'] or episode['trace']['success'] is not False):
        return None
    trace=episode['trace']
    steps=[]
    native_index=0
    policies={p['step']:p for p in policy_selections if p['task_id']==row['task_id'] and not p['validation']}
    for index,step in enumerate(trace['actions']):
        if index in policies:
            p=policies[index]
            if p['action']!=step['action']:
                raise PermissionError('policy action differs from environment trace')
            steps.append(dict(action=step['action'],observation=step['observation'],
                              decision_output='Generated policy '+p['candidate_version'],actor='GENERATED_POLICY'))
        else:
            request_id=row['task_id']+'/'+str(native_index)
            native_index+=1
            response=requests.get(request_id)
            if response is None or response['result']['finish_reason']!='stop':
                raise PermissionError('failure trajectory lacks settled model delivery')
            steps.append(dict(action=step['action'],observation=step['observation'],
                              decision_output=response['result']['text'],actor='MODEL'))
    if not steps or len(steps)!=trace['total_steps'] or native_index!=trace['llm_call_count']:
        raise PermissionError('failure trajectory incomplete')
    public=dict(goal=trace['goal'],initial_observation=initial_observation,steps=steps,won=False)
    code=repr([(x['action'],x['observation']) for x in steps])
    feedback=PublicFeedback('WRONG_ANSWER','Official environment ended without satisfying the public goal.',
                           (canonical(dict(input=trace['goal'],expected='won=true',actual='won=false')),))
    known=[r['payload'] for r in views.records() if r['kind']=='ENVIRONMENT_FAILURE_IMPORTED'
           and r['payload']['source_record_hash']==event['record_hash']]
    if known:
        return known[0]['event_id']
    fact=store.record(stream_id=stream_id,task_id=row['task_id'],family_id='environment-goal-not-completed',
                      stage='environment',code=code,feedback=feedback,observed_at=event['at'],
                      available_from=max(available_from,event['at']),finish_reason='stop',
                      provenance_group_id='game:'+row['game_sha256'])
    payload=dict(event_id=fact['event_id'],source_record_hash=event['record_hash'],
                 game_sha256=row['game_sha256'],public=public)
    views.append('ENVIRONMENT_FAILURE_IMPORTED',payload,time.time())
    return fact['event_id']


def create_candidate(root,compiler,store,views,*,stream_id,evidence_ids,worker_manifest,registry,engineering=False):
    if bool(compiler.provider.mock)!=engineering:
        raise PermissionError('compiler origin differs from experiment mode')
    selected=[]
    known={e['event_id']:e for e in store.visible(time.time(),stream_id)}
    public={r['payload']['event_id']:r['payload']['public'] for r in views.records()
            if r['kind']=='ENVIRONMENT_FAILURE_IMPORTED'}
    for eid in evidence_ids:
        if eid not in known or eid not in public:
            raise PermissionError('unknown source evidence')
        view=public[eid]
        all_steps=view['steps']
        chosen=all_steps if len(all_steps)<=10 else all_steps[:3]+all_steps[-7:]
        def excerpt(text,bound):
            return text if len(text)<=bound else text[:bound]+' [HOST_EXCERPT]'
        selected.append(dict(evidence_id=eid,goal=excerpt(view['goal'],1000),
            initial_observation=excerpt(view['initial_observation'],800),won=False,
            trace_sha256=fingerprint(view),omitted_steps=len(all_steps)-len(chosen),
            steps=[dict(action=step['action'],observation=excerpt(step['observation'],300),
                        decision_output=excerpt(step['decision_output'],300),actor=step['actor']) for step in chosen]))
    job=dict(stream_id=compiler.budget.config['run_id'],family_id=fingerprint(evidence_ids),
             discovery=dict(evidence=selected,shared_cause='UNVERIFIED'))
    induction=replay_train_generation(compiler,job,'induction')
    if induction.get('parse_status'):
        return dict(status='DELIVERY_REJECTED')
    hypothesis=parse_hypothesis(json.loads(induction['specification']))
    save(root/'hypothesis.json',hypothesis)
    if hypothesis['decision']!='PROPOSE':
        return dict(status='NO_MECHANISM')
    job['specification']=canonical(hypothesis)
    generated=replay_train_generation(compiler,job,'candidate')
    if generated.get('parse_status'):
        return dict(status='DELIVERY_REJECTED')
    code=generated['code']
    check=static_check(code)
    save(root/'static.json',check)
    if not check['passed']:
        return dict(status='STATIC_REJECTED',check=check)
    path=root/'generated_policy.py'
    if path.exists() and path.read_text()!=code:
        raise PermissionError('generated source changed')
    path.write_text(code)
    digest=hashlib.sha256(code.encode()).hexdigest()
    prior=[r['payload']['card'] for r in registry.events.records() if r['kind']=='SHADOW_REGISTERED'
           and r['payload']['card']['artifact_sha256']==digest]
    if prior:
        return dict(status='DUPLICATE_SOURCE_REJECTED',artifact_sha256=digest,
                    previous_versions=[r['version'] for r in prior])
    fp=Fingerprint(baseline='alfworld-pure-dynamic',scorer='official-won',
                   model='MOCK' if engineering else generated['model'],dependencies=fingerprint(worker_manifest),
                   protocol=VERSION)
    version=fingerprint([digest,hypothesis,generated['applicability'],evidence_ids,asdict(fp)])
    card=FailureOperator(operator_id=version[:16],version=version,artifact_path=str(path.resolve()),
                         artifact_sha256=digest,evidence_fingerprint=fp,evidence_scope='ALFWORLD_GAME_ID_DISJOINT',
                         evidence_ids=tuple(evidence_ids),source_group_ids=tuple(sorted({known[e]['provenance_group_id'] for e in evidence_ids})),
                         hooks=(ENVIRONMENT_HOOK,),stages=('environment',),allowed_feedback=('ENVIRONMENT_FAILED',),
                         structural_statuses=('ENVIRONMENT_STATE',),allowed_actions=('environment_action',),
                         operator_kind='environment_policy',source_mode='live_online',max_seconds=2)
    if not registry._rows(card):
        registry.register(card,time.time())
    save(root/'artifact.json',dict(card=card.to_dict(),hypothesis=hypothesis,description=generated['description'],
                                  applicability=generated['applicability'],origin='MOCK' if engineering else 'DEEPSEEK',
                                  response_id=generated['id'],response_sha256=generated['response_sha256']))
    return dict(status='SHADOW',card=card.to_dict())
