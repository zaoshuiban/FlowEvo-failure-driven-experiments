"""Explicit freeze/smoke entry for the chronological mathematical stream.
Formal200 execution is blocked until a signed host GO receipt exists; never implicit.
"""
import sys,json,time,hashlib,subprocess,urllib.request,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.math_stream import StreamRuntime,save,read,sha,budget
from failure_evo.math_stream_learning import WindowLearner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.evidence import EvidenceStore
from failure_evo.contracts import fingerprint
from failure_evo.persistent_budget import PersistentBudget
from code_math.private_math_scoring import normalized
DATA=ROOT/'datasets/math_olympiad_three_domain200_20261102'
PREP=ROOT/'runs/math_stream200_preparation_20261102_02'
SMOKE=ROOT/'runs/math_stream200_real_smoke_20261102_02'
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def sources():return sorted(set([Path(__file__).resolve(),ROOT/'scripts/test_math_continuous_stream.py']+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))))
def freeze_plan(tasks,window,max_gate_cases,mode):
    return dict(version='math-continuous-stream-v1',mode=mode,tasks_sha256=fingerprint(tasks),task_count=len(tasks),window=window,
        arms=['G','T','F','R'],model='deepseek-flash',documented_model_version='DeepSeek-V4.1-Flash-1017',temperature=0,
        solver=dict(input_upper=32768,output_upper=4096,calls=2,delivery_profile='concise-v1'),
        learning=dict(input_upper=65536,output_upper=8192,calls_per_window=3,max_candidates=1,max_engineering_revisions=1,functional_revisions=0,
            task_selection='same last window; latest up to6 chronological public questions within16000UTF8 bytes, independent of scores',prior_hypotheses=2),
        r_policy='previous-window-f-call-credit-v1',r_max_extra_calls=3+4*max_gate_cases,max_gate_cases=max_gate_cases,max_tools_per_arm=4000,
        matched_compute='same auxiliary call ceilings; R one-window-lag matches F realized learning+validation calls; not equal actual tokens/Worker time',
        gates='unchanged VersionGate plus MathPublicationGate; absent independent originals/semantic reviews remains Shadow',
        sources={str(f.relative_to(ROOT)):sha(f) for f in sources()},worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),
        source_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),dirty_worktree=True,
        stops=['unknown/pending request','Worker infrastructure fault','leakage/hash/permission failure','hard resource exhaustion','unrecoverable partial journal'],
        normal_outcomes=['no failure','NO_MECHANISM','HYPOTHESIS_ONLY','settled delivery rejection','static rejection','no Gate material','no matches','zero benefit'])
def prepare():
    PREP.mkdir(exist_ok=False);p=read(DATA/'protocol.json');assert sha(DATA/'protocol.json')==read(DATA/'freeze.json')['protocol_sha256'];assert all(sha(DATA/f)==v for f,v in p['files'].items())
    tasks=lines(DATA/'public/tasks.jsonl');meta=lines(DATA/'host/task_metadata.jsonl')
    provenance={m['task_id']:dict(task_id=m['task_id'],source_original_id='UNKNOWN',lineage_id='UNKNOWN',mechanism_family='UNKNOWN',parameter_variant_id='UNKNOWN',dataset_role='PREQUENTIAL_STREAM',
        dataset_record=dict(revision=m['revision'],row=m['row'],source_family=m['source']),template_proxy_sha256=m['template_proxy_sha256'],identity_review='dataset provides source competition family but no verified year/item identity; template hash is not original identity') for m in meta}
    save(PREP/'provenance.json',provenance);save(PREP/'formal_plan.json',freeze_plan(tasks,20,6,'FORMAL200_PENDING_FINAL_DECISION'))
    # Only previously exposed historical tasks; outcome-based smoke selection is explicit engineering diagnosis.
    old=ROOT/'runs/hard140_algorithm_20261028_01';history=read(old/'discovery_outcomes.json');labels={r['task_id']:r for r in read(old/'private/labels.json')}
    eligible=[r for r in history if r['final']['status']=='CONFIRMED_WRONG' and normalized(labels[r['task_id']]['gold_answer'])[0]=='rational']
    selected=sorted(eligible,key=lambda r:r['sequence'])[:4]
    if len(selected)!=4:raise ValueError('insufficient old smoke records')
    public=[r['task'] for r in selected];private=[labels[t['task_id']] for t in public]
    PREP.joinpath('private').mkdir(mode=0o700);save(PREP/'smoke_tasks.json',public);save(PREP/'private/smoke_scores.json',private);(PREP/'private/smoke_scores.json').chmod(0o600)
    ids={t['task_id']:dict(task_id=t['task_id'],source_original_id='UNKNOWN',lineage_id='UNKNOWN',mechanism_family='UNKNOWN',parameter_variant_id='UNKNOWN',dataset_role='EXPOSED_ENGINEERING_SMOKE') for t in public}
    save(PREP/'smoke_provenance.json',ids);save(PREP/'smoke_plan.json',freeze_plan(public,2,0,'OLD_EXPOSED_REAL_SMOKE'))
    save(PREP/'smoke_selection.json',dict(rule='earliest4finalCONFIRMED_WRONG with rational official answers in old hard140, no current model selection',source_sha256=sha(old/'discovery_outcomes.json'),ids=[t['task_id'] for t in public],count=4,window=2,formal200_overlap=bool({t['task_id'] for t in public}&{t['task_id'] for t in tasks})))
    (PREP/'pricing.html').write_bytes(urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing/',timeout=30).read())
    save(PREP/'authorization.json',dict(user_scope='complete zeroAPI acceptance then small real DeepSeek smoke on old tasks; formal200 only after final GO',paid_smoke_authorized=True,formal200_started=False,max_smoke_ledger_accounts_usd=3.627434))
    for f in sources():q=PREP/'frozen_source'/f.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(f.read_bytes())
    save(PREP/'freeze.json',dict(formal_plan_sha256=sha(PREP/'formal_plan.json'),smoke_plan_sha256=sha(PREP/'smoke_plan.json'),data_protocol_sha256=sha(DATA/'protocol.json'),provenance_sha256=sha(PREP/'provenance.json'),smoke_tasks_sha256=sha(PREP/'smoke_tasks.json'),smoke_private_sha256=sha(PREP/'private/smoke_scores.json'),smoke_provenance_sha256=sha(PREP/'smoke_provenance.json')))
    print('FROZEN',PREP,flush=True)
def run_smoke():
    f=read(PREP/'freeze.json');plan=read(PREP/'smoke_plan.json')
    for file,key in [('smoke_plan.json','smoke_plan_sha256'),('smoke_tasks.json','smoke_tasks_sha256'),('private/smoke_scores.json','smoke_private_sha256'),('smoke_provenance.json','smoke_provenance_sha256')]:assert sha(PREP/file)==f[key]
    assert all(sha(ROOT/k)==v for k,v in plan['sources'].items())
    acceptance=read(ROOT/'runs/math_stream200_zero_api_20261102_07/summary.json');assert acceptance['passed']==acceptance['total'] and acceptance['new200_used'] is False
    if not read(PREP/'authorization.json')['paid_smoke_authorized']:raise PermissionError('smoke authorization absent')
    if not SMOKE.exists():SMOKE.mkdir();save(SMOKE/'authorization.json',read(PREP/'authorization.json'))
    stream=StreamRuntime(SMOKE,plan,read(PREP/'smoke_tasks.json'),read(PREP/'private/smoke_scores.json'),read(PREP/'smoke_provenance.json'),backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),learner_factory=lambda s,a:WindowLearner(s,a))
    try:stream.run()
    except BaseException as exc:
        EvidenceStore(SMOKE/'stops.jsonl').append('STOP',dict(type=type(exc).__name__,reason=str(exc),no_resend=True),time.time());raise
    finally:summarize(SMOKE)

def summarize(path):
    path=Path(path);accounts=[];responses=[];arms={};http_rejections=[];unmetered=[]
    for p in path.rglob('*budget.jsonl'):
        b=PersistentBudget.__new__(PersistentBudget);b.path=p
        with b._locked() as rr:b.config=rr[0]['payload']['config'];b.max_calls=b.config['max_calls'];b.max_tokens=b.config['max_tokens'];b.max_tools=b.config['max_tools']
        accounts.append(dict(path=str(p.relative_to(path)),config=b.config,snapshot=b.snapshot()))
    for p in list(path.rglob('requests.jsonl'))+list(path.rglob('provider.jsonl')):
        for r in EvidenceStore(p).records():
            if r['kind']!='RAW_RESPONSE':continue
            raw=r['payload']['response']
            if raw.get('http_status'):
                http_rejections.append(dict(journal=str(p.relative_to(path)),http_status=raw['http_status'],response_sha256=fingerprint(raw),fee_status='UNREPORTED'));continue
            if not isinstance(raw.get('usage'),dict):
                unmetered.append(dict(journal=str(p.relative_to(path)),response_id=raw.get('id'),response_sha256=fingerprint(raw)));continue
            u=raw['usage'];i=u.get('prompt_tokens',u.get('input_tokens',0));o=u.get('completion_tokens',u.get('output_tokens',0));hit=u.get('prompt_cache_hit_tokens',0)
            if type(hit) is not int or not 0<=hit<=i:hit=0
            responses.append(dict(journal=str(p.relative_to(path)),response_id=raw.get('id'),model=raw.get('model'),at=r['at'],finish_reason=raw.get('choices',[{}])[0].get('finish_reason'),input_tokens=i,output_tokens=o,cache_hit_tokens=hit,reasoning_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens',0),peak_quote_usd=((i-hit)*.3+hit*.006+o*1.2)/1e6))
    for a in ('G','T','F','R'):
        states=EvidenceStore(path/a/'task_state.jsonl').records();score=[r['payload']['verdict'] for r in states if r['kind']=='PRIVATE_SCORED'];locks=[r['payload']['lock'] for r in states if r['kind']=='ANSWER_LOCKED'];regs=EvidenceStore(path/a/'registry.jsonl').records();learn=[read(p) for p in (path/a/'learning').glob('*/result.json')] if (path/a/'learning').exists() else []
        cost=[r for r in responses if r['journal'].startswith(a+'/')]
        arms[a]=dict(completed=len(score),statuses=dict(collections.Counter(v['status'] for v in score)),learning_windows=len(learn),learning_statuses=[r['status'] for r in learn],learning_calls=sum(r.get('learning_calls',0) for r in learn),shadow_candidates=sum(r['kind']=='MATH_SHADOW' for r in regs),gate_passes=sum(r['kind']=='MATH_ROUTER_PUBLICATION' for r in regs),actual_operator_executions=sum(r['kind']=='MATH_ROUTER_EXECUTED' for r in regs),distinct_verified_original_reuses=len({r['payload']['original_id'] for r in regs if r['kind']=='MATH_REUSE_OUTCOME'}),fallbacks=sum(l['fallback'] for l in locks),false_accepts='UNVERIFIED_WITHOUT_INDEPENDENT_SEMANTIC_LABELS',responses=len(cost),input_tokens=sum(r['input_tokens'] for r in cost),output_tokens=sum(r['output_tokens'] for r in cost),estimated_peak_usd=sum(r['peak_quote_usd'] for r in cost))
        arms[a]['learning_window_accounted_calls']=arms[a]['learning_calls']
        arms[a]['learning_calls']=sum(r['journal'].endswith('/provider.jsonl') for r in cost)
        arms[a]['learning_calls_basis']='metered received learning responses, including unfinished cumulative windows; connection retries excluded'
        arms[a]['infrastructure_missing']=sum(v['status']=='INFRASTRUCTURE_MISSING' for v in score)
        arms[a]['completed']-=arms[a]['infrastructure_missing']
    paired={}
    for x,y in [('F','G'),('F','T'),('F','R'),('T','G')]:
        def sm(a):return {r['payload']['task_id']:r['payload']['verdict']['status'] for r in EvidenceStore(path/a/'task_state.jsonl').records() if r['kind']=='PRIVATE_SCORED'}
        a,b=sm(x),sm(y);ids={i for i in set(a)&set(b) if a[i]!='INFRASTRUCTURE_MISSING' and b[i]!='INFRASTRUCTURE_MISSING'}
        paired[x+'-'+y]=dict(paired_tasks=len(ids),x_only_correct=sum(a[i]=='CONFIRMED_CORRECT' and b[i]!='CONFIRMED_CORRECT' for i in ids),y_only_correct=sum(b[i]=='CONFIRMED_CORRECT' and a[i]!='CONFIRMED_CORRECT' for i in ids),note='noncorrect includes uncertain/truncated; not all are mathematical errors')
    summary=dict(http_rejections=http_rejections,unmetered_responses=unmetered,arms=arms,pairs=paired,responses=len(responses),tokens=sum(r['input_tokens']+r['output_tokens'] for r in responses),estimated_peak_usd=sum(r['peak_quote_usd'] for r in responses),actual_invoice='UNAVAILABLE',pricing_note='peak quoted rates applied to actual cache-aware usage; actual offpeak invoice can be lower',ledger_charged_or_reserved_usd=sum(a['snapshot']['charged_or_reserved_cost_microusd'] for a in accounts)/1e6,worker_calls=sum(a['snapshot']['tool_calls'] for a in accounts),worker_seconds=sum(a['snapshot']['charged_or_reserved_tool_milliseconds'] for a in accounts)/1000,pending=[k for a in accounts for k in a['snapshot']['unknown_or_pending_requests']],tool_monetary_cost='UNAVAILABLE_NOT_ASSUMED_ZERO',complete=any(r['kind']=='STREAM_COMPLETED' for r in EvidenceStore(path/'stream.jsonl').records()))
    plan_path=path/'execution_plan.json'
    if plan_path.exists() and read(plan_path).get('experiment_mode')=='LEARNING_DIAGNOSTIC':
        summary['research_scope']='DIAGNOSTIC'
    summary['not_sent_requests']=[k for a in accounts for k in a['snapshot']['not_sent_requests']]
    summary['connection_attempts']=sum(a['snapshot']['connection_attempts'] for a in accounts)
    summary['network_accounting']='NOT_SENT has zero model calls/tokens/fee; UNKNOWN retains full reservation; connections are not model requests'
    if (path/'continuation.json').exists():
        m=read(path/'continuation.json')
        summary['continuation_scope']=dict(parent=m.get('parent'),missing_sequences=m.get('missing_sequences'),
            inherited_costs_included=True,accounting='Inherited account journals copied once; original spend and UNKNOWN reservations remain included, not added a second time.')
    save(path/'cost_accounts.json',accounts);save(path/'response_usage.json',responses);save(path/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','smoke','summary']);p.add_argument('--path',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='smoke':run_smoke()
    else:summarize(a.path or SMOKE)
