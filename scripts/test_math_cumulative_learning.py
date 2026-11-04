"""Zero paid API: explicit mocks/old engineering tasks, actual Linux Worker."""
import json,time,sys,copy,tempfile
from pathlib import Path
from math_candidate_mock import assessment
from failure_evo.math_cumulative_stream import CumulativeStream,DEFAULTS,validate_config
from failure_evo.math_cumulative import CumulativeMemory,CumulativeQueue,excerpt
from failure_evo.math_cumulative_learning import ReviewedRelease,AssociationAdapter
from failure_evo.contracts import fingerprint
from failure_evo.math_stream import save,read
from failure_evo.evidence import EvidenceStore
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import PublicMathTask
from test_math_continuous_stream import raw,gen_sender,solve_sender,reviewed
from run_math_manual_lifecycle import problem
from run_math_v3_development import ROOT,WORKER,IMAGE
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(tempfile.mkdtemp(prefix='flowevo-cumulative-'))
OUT.mkdir(parents=True,exist_ok=True);checks={};wires=[]
def generator(arm,role='ANSWER',cause='SUSPECTED'):
    base=gen_sender(arm)
    def send(w):
        data=json.loads(w['messages'][1]['content']);wires.append((arm,copy.deepcopy(data)))
        if 'candidate_clusters' not in data:
            if 'hypothesis' not in data:
                refs=[e['evidence_id'] for e in data['learning_evidence_bundle']['evidence']]
                return raw(json.dumps(assessment(refs,status=cause,role=role)))
            return base(w)
        desc=[];links=[]
        for e in data['evidence']:
            desc.append(dict(evidence_id=e['evidence_id'],task_structure='MOCK structure',observable_symptom='MOCK observation',possible_cause='UNVERIFIED MOCK',possible_correction='MOCK fixture',uncertainty='engineering only'))
            links.append(dict(evidence_id=e['evidence_id'],relation='SUPPORT',reason='MOCK evidence relation',evidence_quote=e['problem'],new_information=True))
        return raw(json.dumps(dict(descriptions=desc,clusters=[dict(cluster_id=data['candidate_clusters'][0]['cluster_id'] if data['candidate_clusters'] else 'NEW',hypothesis=dict(mechanism='MOCK finite computation',uncertainty='engineering only',applicability='fixture',exclusions='other',input_output='fixture parameter'),assessment=assessment([e['evidence_id'] for e in data['evidence']],status=cause,role=role),links=links)])))
    return send

def run_case(name,mode='workflow',gate=False,role='ANSWER',cause='SUSPECTED'):
    tasks=[dict(task_id='fixture-'+str(i),problem=problem(i)) for i in range(1,7)]
    labels=[dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),gold_answer=str(sum(range(1,i+2)))) for i,t in enumerate(tasks)]
    lineage={t['task_id']:dict(source_original_id='MOCK_'+t['task_id']) for t in tasks}
    cfg=dict(DEFAULTS,max_association_jobs=2,max_generation_jobs=1,comparison=mode)
    if mode=='paired_information':cfg['paired_packs']=[dict(after_sequence=2,task_ids=[t['task_id'] for t in tasks[:2]])]
    plan=dict(tasks_sha256=fingerprint(tasks),window=2,r_policy='previous-window-f-call-credit-v1',r_max_extra_calls=27,max_gate_cases=6,max_tools_per_arm=1200,sources={},cumulative=cfg)
    def release(s,a):
        rr=ReviewedRelease(s,a,reviewed if gate else None);rr.sender=solve_sender(a);return rr
    def make():return CumulativeStream(OUT/name,plan,tasks,labels,lineage,backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),engineering=True,sender_factory=solve_sender,learning_sender_factory=lambda a:generator(a,role,cause),release_factory=release)
    s=make();s.run();before=len(wires);make().run();checks[name+'_resume_no_new_learning']=len(wires)==before
    checks[name+'_all_tasks_completed']=read(s.path/'progress.json')['last_sequence']==6
    for a in ('T','F'):
        reg=s.arms[a]['registry'].events.records();checks[name+'_'+a+'_shadow']=any(x['kind']=='MATH_SHADOW' for x in reg)
        facts=s.arms[a]['learner'].memory.facts(6)
        checks[name+'_'+a+'_raw_persists']=len(facts)>0
        if a=='T':checks[name+'_T_no_grades']=all('correct' not in f and 'trajectory' not in f for f in facts.values())
    if gate:
        checks['actual_gate_publication']=any(x['kind']=='MATH_ROUTER_PUBLICATION' for x in s.arms['F']['registry'].events.records())
        checks['future_execution']=any(x['kind']=='MATH_ROUTER_EXECUTED' and x['payload']['sequence']>1 for x in s.arms['F']['registry'].events.records())
    else:checks[name+'_no_automatic_permission']=not any(x['kind']=='MATH_ROUTER_PUBLICATION' for x in s.arms['F']['registry'].events.records())
    return s
s=run_case('shadow');paired=run_case('paired','paired_information');published=run_case('published',gate=True)
diagnostic=run_case('diagnostic',role='DIAGNOSTIC',cause='UNSUPPORTED')
checks['unsupported_cause_can_generate_diagnostic']=all(any(read(p)['status']=='SHADOW_DIAGNOSTIC_ONLY' for p in (diagnostic.path/a/'learning').rglob('result.json')) for a in ('T','F'))
checks['diagnostic_not_answer_scored']=all(x['combined_source']['status']=='DIAGNOSTIC_NOT_ANSWER_SCORED' for p in diagnostic.path.rglob('source_execution.json') for x in read(p))
checks['diagnostic_not_published']=not any(r['kind']=='MATH_ROUTER_PUBLICATION' for a in ('T','F') for r in diagnostic.arms[a]['registry'].events.records())
checks['paired_shared_question_sets']=read(next((paired.path/'T/learning').rglob('public_input.json')))['questions']==read(next((paired.path/'F/learning').rglob('public_input.json')))['questions']
checks['real_worker_execution']=any(x['kind']=='V3_COMPONENT_EXECUTED' for p in OUT.rglob('worker.jsonl') for x in EvidenceStore(p).records())
# Host clipping retains answer suffix and explicit provenance.
e=excerpt('start'*600+'The answer is 9182',100)
checks['fragment_keeps_final_answer']='9182' in e['text'] and e['omission']=='HOST_MIDDLE_OMISSION'
# Queue regression: counts alone must not relaunch identical evidence.
learner=s.arms['F']['learner'];mem=learner.memory;q=learner.queue
jobs=q.schedule(mem,6,budget_available=True);checks['no_repeated_same_evidence']=all(j['new_evidence_ids'] for j in jobs)
checks['no_future_evidence']=all(f['sequence']<=2 for f in mem.facts(2).values())
checks['T_wire_no_failure_fields']=all('correct' not in json.dumps(w) and 'trajectory' not in json.dumps(w) for a,w in wires if a=='T' and 'candidate_clusters' in w)
try:
 validate_config(dict(DEFAULTS,comparison='paired_information',paired_packs=[dict(after_sequence=1,task_ids=['future'])]),[dict(task_id='now',problem='x'),dict(task_id='future',problem='y')])
except ValueError:checks['future_paired_pack_rejected']=True
# No authorization: no transport invoked.
learner.stream.engineering=False
try:learner._authorize()
except PermissionError:checks['paid_call_denied_without_new_authorization']=True
finally:learner.stream.engineering=True
save(OUT/'acceptance.json',dict(checks=checks,passed=sum(checks.values()),total=len(checks),paid_api_calls=0,worker='actual Docker Linux',origin='ENGINEERING_MOCK_NOT_LEARNING_EVIDENCE'))
print(OUT);print(checks);assert all(checks.values())
