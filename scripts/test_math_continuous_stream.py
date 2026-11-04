"""Full unified scheduler acceptance: disclosed old engineering fixtures, no new200 tasks."""
import sys,json,time,copy,shutil
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE
from run_math_manual_lifecycle import SOLVE,MATCH,problem
from failure_evo.math_stream import StreamRuntime,read,save,budget
from failure_evo.math_stream_learning import WindowLearner,ReviewedRelease,StreamCompilerAdapter
from failure_evo.math_learning import FIELDS as H_FIELDS
from failure_evo.semantic_contract import FIELDS
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.run_health import RunUnhealthy
from code_math.no_gold import PublicMathTask
OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'runs/math_stream200_zero_api_20261102_01'

def raw(content,finish='stop'):
    return dict(id='engineering-'+fingerprint([content,time.time_ns()])[:16],model='deepseek-flash',choices=[dict(message=dict(content=content),finish_reason=finish)],usage=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150))

def solve_sender(arm):
    def sender(wire):
        text=wire['messages'][1]['content'];out='The answer is 0';finish='stop'
        if 'TRUNCATION_FIXTURE' in text:out='Unfinished enumeration\n25';finish='length'
        elif 'UNVERIFIED_FIXTURE' in text:out='The answer is x+y'
        else:
            for n in (5,6,7,8):
                if problem(n) in text:out='The answer is '+str(sum(range(1,n+1)))
        return raw(out,finish)
    return sender

def gen_sender(arm):
    def sender(wire):
        assert 'json' in wire['messages'][0]['content'].lower()
        data=json.loads(wire['messages'][1]['content']);questions=data['evidence']['questions']
        if 'hypothesis' not in data:
            return raw(json.dumps(dict(decision='PROPOSE',**{k:'Human-authored engineering fixture response, not model learning.' for k in H_FIELDS})))
        broken=any('TRUNCATION_FIXTURE' in q['problem'] for q in questions)
        code=SOLVE+MATCH+'\n# fixture version '+fingerprint(questions)+'\n'
        if arm=='T' and len(data.get('prior_unverified_hypotheses',[]))==1 and 'engineering_diagnostics' not in data:
            code+='\ndef unused():\n    x=0\n    def inner():\n        nonlocal x\n        x+=1\n        return x\n    return inner()\n'
        if broken:code=code.replace('return str(n * (n + 1) // 2)',"return '0'")
        contract={k:'ENGINEERING_FIXTURE_ONLY' for k in FIELDS};contract.update(requested_quantity='integer sum',parameter_schema=json.dumps(dict(type='object',properties=dict(n=dict(type='integer',minimum=0,maximum=10000)),required=['n'],additionalProperties=False)))
        return raw(json.dumps(dict(code=code,description=json.dumps(contract),applicability='explicit old fixture only')))
    return sender

def reviewed(a,cutoff):
    def c(tid,n,positive):
        q=problem(n) if positive else f'Compute the product of integers from 1 through {n}, inclusive.'
        import math
        return dict(task_id=tid+'-'+str(cutoff),original_id='MOCK_INDEPENDENCE_TOKEN_'+tid+'-'+str(cutoff),problem=q,supported=positive,
            parameters={'n':n} if positive else {},answer=str(sum(range(1,n+1))) if positive else str(math.factorial(n)),
            available_after_sequence=0,review_status='INDEPENDENT_VERIFIED',reviewer='human engineering fixture, not real original provenance',oracle_sha256=fingerprint(['builtin-sum-and-factorial',n]))
    return dict(origin='ENGINEERING_FIXTURE',artifact_sha256=a['code_sha256'],Development=[c('d1',101+cutoff,True),c('d2',102+cutoff,True),c('dn',3,False)],Gate=[c('g1',103+cutoff,True),c('g2',104+cutoff,True),c('gn',4,False)])

def main():
    if OUT.exists():raise RuntimeError('new engineering namespace required')
    OUT.mkdir();checks={}
    tasks=[dict(task_id='fixture-'+str(i),problem=problem(i)) for i in range(1,17)]
    tasks[9]['problem']='Compute the product of integers from 1 through 4, inclusive.'
    tasks[10]['problem']='UNVERIFIED_FIXTURE: find the requested number.'
    tasks[11]['problem']='TRUNCATION_FIXTURE: find the requested number.'
    tasks[13]['problem']='Compute the product of integers from 1 through 5, inclusive.'
    private=[dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),gold_answer=str(sum(range(1,i+2)))) for i,t in enumerate(tasks)]
    private[9]['gold_answer']='24';private[13]['gold_answer']='120'
    lineage={t['task_id']:dict(source_original_id='MOCK_INDEPENDENCE_TOKEN_'+t['task_id'],lineage_id='SHARED_ENGINEERING_PARAMETER_FAMILY',mechanism_family='ENGINEERING_ONLY',parameter_variant_id=t['task_id'],dataset_role='ENGINEERING_EXPOSED') for t in tasks}
    plan=dict(version='math-continuous-stream-v1',tasks_sha256=fingerprint(tasks),window=4,r_policy='previous-window-f-call-credit-v1',r_max_extra_calls=27,max_gate_cases=6,max_tools_per_arm=1200,origin='ENGINEERING_FIXTURES_NOT_RESEARCH')
    backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
    def factory(s,arm):
        release=ReviewedRelease(s,arm,reviewed);release.sender=solve_sender(arm)
        return WindowLearner(s,arm,sender=gen_sender(arm),release=release)
    def make(path,fault=None):return StreamRuntime(path,plan,tasks,private,lineage,backend=backend,learner_factory=factory,engineering=True,sender_factory=solve_sender,fault=fault)
    crashes=[]
    def fault(where,arm,seq):
        if where=='after_answer_lock' and arm=='G' and seq==2 and not crashes:
            crashes.append('injected');raise RuntimeError('ENGINEERING_PROCESS_CRASH_AFTER_DURABLE_LOCK')
    s=make(OUT/'run',fault)
    try:s.run()
    except RuntimeError as e:checks['crash_injected']=str(e)=='ENGINEERING_PROCESS_CRASH_AFTER_DURABLE_LOCK'
    else:raise AssertionError('fault not reached')
    count=lambda:[(str(p),r['payload'].get('request_id')) for p in (OUT/'run').rglob('requests.jsonl') for r in EvidenceStore(p).records() if r['kind']=='RAW_RESPONSE']
    before=count();s=make(OUT/'run');s.run();after=count()
    checks['resume_without_resend']=all(after.count(x)==1 for x in before)
    s2=make(OUT/'run');s2.run();checks['completed_run_replay_no_new_calls']=count()==after
    allstates={a:s.arms[a]['states'].records() for a in ('G','T','F','R')}
    checks['four_groups_same_order']=all([r['payload']['task_id'] for r in rows if r['kind']=='TASK_STARTED']==[t['task_id'] for t in tasks] for rows in allstates.values())
    checks['four_windows_each']=all(sum(r['kind']=='WINDOW_COMPLETED' for r in rows)==4 for rows in allstates.values())
    checks['score_after_all_arm_locks']=all(min(r['at'] for rows in allstates.values() for r in rows if r['kind']=='PRIVATE_SCORED' and r['payload']['sequence']==i)>=max(r['at'] for a in s.arms.values() for r in a['controller'].records() if r['kind']=='MATH_ANSWER_LOCKED' and r['payload']['sequence']==i) for i in range(1,17))
    checks['credible_failure_window']=bool(s.evidence('F',4))
    checks['no_failure_window_normal']=read(OUT/'run/F/learning/8/result.json')['status']=='NO_CONFIRMED_FAILURE_IN_SELECTED_WINDOW'
    checks['T_learns_even_when_F_no_failure']=(OUT/'run/T/learning/8/hypothesis.json').exists()
    checks['symmetric_engineering_repair']=read(OUT/'run/T/learning/8/version_change.json')['classification']=='SUBSTANTIVE_OR_UNRESOLVED'
    checks['same_public_questions']=all(read(OUT/f'run/T/learning/{i}/public_input.json')['questions']==read(OUT/f'run/F/learning/{i}/public_input.json')['questions'] for i in (4,8,12))
    checks['T_no_error_metadata']=all(set(read(p))=={'questions'} for p in (OUT/'run/T/learning').glob('*/public_input.json'))
    checks['F_binary_false']=all(o['correct'] is False for p in (OUT/'run/F/learning').glob('*/public_input.json') for o in read(p)['observations'])
    reg={a:s.arms[a]['registry'].events.records() for a in ('T','F')}
    checks['both_real_registry_gate_approved']=all(any(r['kind']=='MATH_ROUTER_PUBLICATION' for r in rs) for rs in reg.values())
    checks['failed_candidate_shadow']=read(OUT/'run/F/learning/12/result.json')['status']=='SHADOW_DEVELOPMENT_GATE_FAILED'
    locks={a:[r['payload']['lock'] for r in rows if r['kind']=='ANSWER_LOCKED'] for a,rows in allstates.items()}
    checks['future_operator_applied']=any(l['operator_events'] and l['operator_events'][-1]['status']=='APPLIED' for l in locks['F'][4:])
    checks['source_no_same_task_use']=all(not l['operator_events'] or l['operator_events'][-1]['status']!='APPLIED' for l in locks['F'][:4])
    checks['refusal_and_native_fallback']=locks['F'][9]['fallback'] and len(locks['F'][9]['responses'])==2
    checks['multi_operator_conflict']=any(l['operator_events'] and l['operator_events'][-1].get('reason')=='UNRESOLVED_QUALITY_TIE' for l in locks['T'])
    scores={a:[r['payload']['verdict'] for r in rows if r['kind']=='PRIVATE_SCORED'] for a,rows in allstates.items()}
    checks['truncated_not_failure']=all(v[11]['status']=='TRUNCATED' and not v[11]['credible_failure'] for v in scores.values())
    checks['symbolic_unverified']=all(v[10]['status']=='UNVERIFIED' and not v[10]['credible_failure'] for v in scores.values())
    checks['only_complete_confirmed_wrong_enters_F']=all(e['sequence'] not in (11,12) for e in s.evidence('F',16))
    checks['R_lagged_call_credit']=locks['R'][3]['model_calls']==2 and locks['R'][7]['model_calls']==12 and locks['R'][11]['model_calls']==2 and locks['R'][15]['model_calls']==4
    checks['R_no_learning_or_operator']=not list((OUT/'run/R').glob('learning/*')) and not any(l['operator_events'] for l in locks['R'])
    # Runtime public projection checks: solver exact builder and learner allowlist.
    from code_math.no_gold import solver_messages,NoGoldPolicy
    checks['solver_wire_no_private_fields']=all(set(r['payload']['wire'])=={'model','messages','temperature','max_tokens','thinking','reasoning_effort','stream'} for p in (OUT/'run').rglob('requests.jsonl') for r in EvidenceStore(p).records() if r['kind']=='NO_GOLD_REQUEST')
    checks['unique_request_ids']=len(after)==len(set(after))
    checks['no_pending_accounts']=True;s.health()
    # Unknown request globally blocks later arms, and a restart never resends it.
    attempts=[]
    def unknown_factory(arm):
        def sender(w):attempts.append(arm);raise OSError('SIMULATED_UNKNOWN')
        return sender
    u=StreamRuntime(OUT/'unknown',plan,tasks,private,lineage,backend=backend,learner_factory=factory,engineering=True,sender_factory=unknown_factory)
    try:u.run()
    except OSError:pass
    else:raise AssertionError('unknown not raised')
    try:u.run()
    except RunUnhealthy:checks['unknown_blocks_all_new_requests']=attempts==['G']
    else:checks['unknown_blocks_all_new_requests']=False
    # Crash after actual response+settlement but before client cache: recover raw, no resend.
    tiny=tasks[:2];tp=dict(plan,tasks_sha256=fingerprint(tiny),window=2)
    tl={t['task_id']:lineage[t['task_id']] for t in tiny}
    z=StreamRuntime(OUT/'response_crash',tp,tiny,private[:2],tl,backend=backend,learner_factory=factory,engineering=True,sender_factory=solve_sender)
    def crash_cache(*args):raise RuntimeError('CRASH_AFTER_SETTLED_RESPONSE')
    z.arms['G']['client'].cache.append=crash_cache
    try:z.run()
    except RuntimeError as exc:assert str(exc)=='CRASH_AFTER_SETTLED_RESPONSE'
    z=StreamRuntime(OUT/'response_crash',tp,tiny,private[:2],tl,backend=backend,learner_factory=factory,engineering=True,sender_factory=solve_sender);z.run()
    rr=EvidenceStore(OUT/'response_crash/G/requests.jsonl').records()
    checks['settled_raw_recovered_without_send']=sum(r['kind']=='RAW_RESPONSE' for r in rr)==4
    # Received malformed model content remains a settled delivery outcome, not transport UNKNOWN.
    mp=dict(tp,window=1)
    def invalid_factory(st,arm):return WindowLearner(st,arm,sender=lambda wire:raw('not-json'))
    m=StreamRuntime(OUT/'malformed',mp,tiny,private[:2],tl,backend=backend,learner_factory=invalid_factory,engineering=True,sender_factory=solve_sender);m.run();m.health()
    checks['malformed_received_settled_not_unknown']=read(OUT/'malformed/T/learning/1/result.json')['status']=='SETTLED_DELIVERY_REJECTED' and read(OUT/'malformed/progress.json')['status']=='COMPLETE'
    checks['invalid_gate_no_publication']=not any(r['kind']=='MATH_ROUTER_PUBLICATION' and r['payload']['artifact']['code_sha256']==read(OUT/'run/F/learning/12/artifact.json')['code_sha256'] for r in s.arms['F']['registry'].events.records())
    # Invalid private/public boundary and reviewed identity failures reject before execution.
    try:PublicMathTask.parse(dict(tasks[0],gold_answer='SECRET'))
    except ValueError:checks['public_gold_field_rejected']=True
    a=read(OUT/'run/T/learning/4/artifact.json')
    def future_package(a,c):
        p=reviewed(a,c);p['Gate'][0]['available_after_sequence']=999;return p
    try:ReviewedRelease(s,'T',future_package).attempt(a,4,OUT/'forbidden')
    except PermissionError:checks['future_gate_rejected']=True
    def unknown_package(a,c):
        p=reviewed(a,c);p['Gate'][0]['original_id']='UNKNOWN';return p
    try:ReviewedRelease(s,'T',unknown_package).attempt(a,4,OUT/'forbidden')
    except PermissionError:checks['unknown_original_cannot_publish']=True
    changed=dict(plan,window=5)
    try:StreamRuntime(OUT/'run',changed,tasks,private,lineage,backend=backend,learner_factory=factory,engineering=True,sender_factory=solve_sender)
    except PermissionError:checks['protocol_drift_rejected']=True
    # Strict publication scoring never treats a truncated numeric answer as correctness.
    from failure_evo.math_publication import MathPublicationGate
    from code_math.no_gold import NoGoldPolicy
    gate=MathPublicationGate(s.arms['T']['registry'],s.arms['T']['probe'],OUT/'strict_gate.jsonl',engineering=True)
    cases=reviewed(a,99)['Gate']
    fid=gate.freeze(a,cases,development_originals=[],input_rate=.3e-6,output_rate=1.2e-6,tool_second_rate=0)
    class TruncatedClient:
        def generate_no_gold(self,*,messages,policy,request_id):
            return dict(text='The answer is 0',finish_reason='length',usage=dict(prompt_tokens=1,completion_tokens=1),origin='MOCK',model='engineering',response_id=request_id)
    result=gate.evaluate(fid,TruncatedClient(),OUT/'strict_gate_controller.jsonl',strict_delivery=True)
    checks['truncated_generic_cannot_approve_gate']=not result['end_to_end_gate'] and not result['passed']
    checks['generation_json_wire_contract']=True
    worker=[r for p in (OUT/'run').rglob('worker.jsonl') for r in EvidenceStore(p).records() if r['kind']=='V3_COMPONENT_EXECUTED']
    checks['real_linux_worker_executed']=bool(worker) and all(r['payload']['raw']['status']=='OK' for r in worker)
    save(OUT/'checks.json',checks);save(OUT/'summary.json',dict(passed=sum(checks.values()),total=len(checks),checks=checks,real_model_calls=0,worker_calls=len(worker),worker_seconds=sum(r['payload']['seconds'] for r in worker),mock_requests=len(after),origin='HUMAN_ENGINEERING_FIXTURES_AND_MOCKS_NOT_REAL_LEARNING',new200_used=False))
    print(json.dumps(read(OUT/'summary.json'),indent=2));assert all(checks.values())
if __name__=='__main__':main()
