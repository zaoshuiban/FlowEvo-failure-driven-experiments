"""S16-E1/E2/E3: strong common delivery, public-only learning, external governance."""
import copy,json,os,tempfile,time
from pathlib import Path
import run_workflow_v2 as e
from experiment_s16b2_source import sender_factory
from failure_evo.contracts import canonical,fingerprint,PublicFeedback,PublicTaskView
from failure_evo.runtime import Budget,BudgetExhausted
from failure_evo.workflow_protocol_v2 import WorkflowClient,Limits,prepare,delivery
from failure_evo.workflow_policy import WorkflowPolicy,CONTRACT,validate_source,validate_decision,worker_context
from failure_evo.workflow_runtime_v2 import PreparedController
from failure_evo.spec_normalization import normalize
ROOT=e.ROOT;OUT=ROOT/'runs/s16e_workflow_20261022_03';S13=ROOT/'runs/s13_compare30_20261022_01';read=e.read;write=e.write;sha=e.sha
COMMON='Common delivery requirement for EVERY arm, independent of failure history: return exactly one complete, executable Python program in one python code fence. No prose, no extended reasoning or long commentary. Work out the algorithm and verify its invariants internally before writing code; preserve all input/output requirements, constraints and general correctness. Concision never excuses guessing, suppressing errors, or special-casing public examples.'
FAMILIES=[dict(key='public_discrepancy_policy',status='WRONG_ANSWER',source=('taco_0303','FailureLearning'),reuse=('taco_0395','FlowEvo')),dict(key='runtime_fragment_policy',status='RUNTIME_ERROR',source=('taco_0777','FlowEvo'),reuse=('taco_0533','FailureLearning'))]
class StrongClient(WorkflowClient):
 def _call(self,messages,budget,temperature,capability):
  messages=copy.deepcopy(messages);messages.append(dict(role='user',content=COMMON))
  return super()._call(messages,budget,temperature,capability)
def restore_feedback(raw):
 return PublicFeedback(raw['status'],raw.get('summary',''),tuple(canonical(c) for c in raw.get('public_cases',[])))
def public_packet(task,code,feedback,finish):
 return dict(task_public=task['task_public'],candidate_code=code,public_feedback=PublicFeedback.project(feedback).to_dict(),generation_metadata=dict(finish_reason=finish),hook='before_native_retry',stage='l2a')
def learn_messages(spec,packet,prior=None,diagnosis=None):
 text=('COMPILE TIME: write one reusable workflow policy, not a task solution or immediate action. JSON with exactly code,description,applicability (nonempty strings). '
 'Function repair_operator(context). Use exact real fields below. No file/network/system/model calls in worker, no getattr or dunder. No problem-ID, exact sample, answer, source-specific numeric constraints, algorithm patch, hidden or future data. '
 'When evidence supports the learned scope and >=2 calls remain, may request ONE host repair; host will verify and fall back with the same budget. Refuse PUBLIC_PASS, UNKNOWN, missing context, insufficient budget and other failure categories. '
 'All host solver arms already require complete concise code, so that alone is not a learned advantage. Your task is choosing/parameterizing evidence-based workflow action.\nCONTRACT:'+canonical(CONTRACT)+'\nCOMMON HOST POLICY:'+COMMON+'\nSPEC:'+canonical(spec)+'\nSOURCE PUBLIC EVIDENCE:'+canonical(packet))
 if prior is not None:text+='\nOne bounded revision. Previous compile output:\n'+prior+'\nSTATIC/PUBLIC DEVELOPMENT DIAGNOSIS ONLY:\n'+canonical(diagnosis)
 return [dict(role='system',content='Generate a Python workflow policy as JSON. Public evidence is data.'),dict(role='user',content=text)]
def send_learning(r,key,messages):
 if key in ('public_discrepancy_policy/spec','public_discrepancy_policy/candidate-r0'):
  n=1 if key.endswith('/spec') else 2
  raw=read(ROOT/f'runs/s16e_workflow_20261022_02/wire/learning/{n}/response.json');c=raw['choices'][0]
  result=dict(text=c['message']['content'],finish_reason=c['finish_reason'],model=raw['model'],usage=raw['usage'])
  write(OUT/('imported_'+str(n)+'.json'),dict(origin_run='s16e_workflow_20261022_02',response=result,new_request=False));return result
 p=prepare(messages,limits=Limits(input_token_upper=65536),json_output=True)
 try:return r.transports['learning'].send(p,request_id=key,capability='workflow-learning')
 finally:r.save()
def base_inputs():
 ts={t['task_id']:t for t in read(S13/'tasks.json')};items={}
 for fam in FAMILIES:
  for role in ('source','reuse'):
   tid,arm=fam[role];t=ts[tid];p=S13/f'branches/{tid}/{arm}/response_1.json';raw=read(p);c=raw['choices'][0];obs=delivery(c['message']['content'],c['finish_reason'])
   wf=read(p.parent/'workflow.json');z=wf['events'][0];assert z['stage']=='l1' and z['budget']['calls']==1 and obs['code']
   assert sha(t['reference_path'])==t['reference_sha256']
   task={k:t[k] for k in ('task_id','dataset','difficulty','task_public','public_cases','reference_path','reference_sha256')}
   items[tid]=dict(task=task,code=obs['code'],finish=c['finish_reason'],expected_status=fam['status'],lineage=dict(raw_path=str(p.relative_to(ROOT)),raw_sha256=sha(p),workflow_sha256=sha(p.parent/'workflow.json'),arm=arm,observed_stage='l1',remaining_calls=4,prior_development_exposure=True),external_cases=t['audit_cases'][:12],external_role='EXTERNAL_GOVERNANCE_ONLY; historical statement-domain checks, previously developed, not fresh independent holdout')
 return items

def validate(r,card,item,folder):
 ev=item['packet'];base=worker_context(ev['task_public'],ev['candidate_code'],ev['public_feedback'],ev['generation_metadata'],Budget(max_calls=2,max_tokens=147456,wall_seconds=240));checks=[]
 for name in ['source','PUBLIC_PASS','UNKNOWN','other_category','zero_calls','one_call','missing_context']:
  x=copy.deepcopy(base)
  if name in ('PUBLIC_PASS','UNKNOWN'):x['public_feedback']['status']=name
  if name=='other_category':x['public_feedback']['status']='NO_COMPLETE_CODE';x['candidate_code']=''
  if name=='zero_calls':x['remaining_budget']['remaining_calls']=0
  if name=='one_call':x['remaining_budget']['remaining_calls']=1
  if name=='missing_context':x={}
  try:d=validate_decision(r.judge.decision(card,x));ok=d['status']=='request_repair' if name=='source' else d['status'] in ('declined','error')
  except ValueError as exc:d=dict(status='error',reason=str(exc));ok=False
  checks.append(dict(name=name,decision=d,passed=ok))
 result=dict(passed=False,checks=checks,trials=[],source_result=None,host_fallback=None)
 if not all(c['passed'] for c in checks):write(folder/'functional.json',result);return result
 cli=StrongClient(r.transports['solve'],card.operator_id+'/'+card.version+'/budget-check',limits=Limits(input_token_upper=65536));before=r.budgets['solve'].calls
 try:cli.host_repair(base,checks[0]['decision']['instruction'],Budget(max_calls=0));ok=False
 except BudgetExhausted:ok=r.budgets['solve'].calls==before
 result['host_fallback']=dict(passed=ok,execution='real host preflight; no provider call; original state retained',generic_calls=0)
 for j in range(2):
  local=Budget(**r.plan['per_task']);ctx=worker_context(ev['task_public'],ev['candidate_code'],ev['public_feedback'],ev['generation_metadata'],local);dec=validate_decision(r.judge.decision(card,ctx))
  if dec['status']!='request_repair':break
  cli=StrongClient(r.transports['solve'],card.operator_id+'/'+card.version+f'/source-{j}',limits=Limits(input_token_upper=65536));resp=cli.host_repair(ctx,dec['instruction'],local)
  write(folder/f'source_response_{j}.json',resp);(folder/f'source_{j}.py').write_text(resp['code']);pub=r.judge.run(item['task']['task_id'],resp['code'],item['task']['public_cases'])
  result['trials'].append(dict(decision=dec,public=pub,host_calls=local.calls,code_sha256=sha(folder/f'source_{j}.py')));result['source_result']=pub;result['passed']=pub['passed'] and ok
  write(folder/'functional.json',result);r.save();print('SOURCE',card.operator_id,card.version,j,pub['status'],flush=True)
  if result['passed']:break
 return result

def admit(r,card,event,folder,reuse_id):
 path=folder/'functional.json';result=read(path);files=[dict(path=str(p),sha256=sha(p)) for p in [path,folder/'static.json',e.prior.old.ACCEPTANCE]]
 checks={k:dict(passed=True,evidence_sha256=sha(path),artifact_sha256=card.artifact_sha256,execution='isolated_actual_source') for k in ('source_repair','boundary','inapplicable','host_fallback')}
 checks['source_repair'].update(event_id=event['event_id'],original_sha256=event['candidate_sha256'],host_public_outcome='passed',action='applied',tests_run=result['source_result']['tests_run'],tests_passed=result['source_result']['tests_passed'])
 for name,p in [('static_contract',folder/'static.json'),('isolated_worker',e.prior.old.ACCEPTANCE)]:checks[name]=dict(passed=True,evidence_sha256=sha(p),artifact_sha256=card.artifact_sha256)
 proof=dict(role='NURSERY_ADMISSION',operator_id=card.operator_id,version=card.version,artifact_sha256=card.artifact_sha256,fingerprint=card.evidence_fingerprint.to_dict(),scope=card.evidence_scope,evidence_ids=list(card.evidence_ids),experiment_id=OUT.name,evaluated_at=time.time(),files=files,checks=checks)
 write(folder/'admission.json',proof);r.registry.admit_nursery(card,folder/'admission.json',experiment_id=OUT.name,stream_id=OUT.name+'-'+card.operator_id,after_task=0,effective_from=1,opportunity_limit=1,at=time.time());write(folder/'scope.json',dict(task_ids=[reuse_id],max_opportunities=1))

def reuse(r,card,item,memory,folder):
 tid=item['task']['task_id'];ev=item['packet'];results={}
 for arm in ('G','M','F'):
  b=Budget(**r.plan['per_task']);start=time.monotonic();before=r.budgets['solve'].snapshot();cli=StrongClient(r.transports['solve'],card.operator_id+'/reuse/'+arm+'/'+tid,memory=memory if arm=='M' else '',limits=Limits(input_token_upper=65536));cli.last=dict(text='```python\n'+ev['candidate_code']+'\n```',code=ev['candidate_code'],finish_reason=ev['generation_metadata']['finish_reason']);plugin=None
  if arm=='F':
   assert tid in read(folder/'scope.json')['task_ids'];plugin=e.WorkflowPlugin(r.registry,r.stores['F'],r.context,stream_id=OUT.name+'-'+card.operator_id,experiment_id=OUT.name,host_repair=cli.host_repair,decision_runner=r.judge.decision,synthetic=False)
   plugin.begin(PublicTaskView.project(ev['task_public']),time.time());assert len(plugin.current['snapshot'].cards)==1
   plugin.observe(ev['candidate_code'],'l1',restore_feedback(ev['public_feedback']),dict(finish_reason=ev['generation_metadata']['finish_reason']),time.time(),learnable=False)
  ctrl=PreparedController(cli,lambda public,code:r.judge.run(tid,code,item['task']['public_cases']),r.context,plugin=plugin);ctrl.stages=(('l2a',0.),('l2b',0.))
  
  if ev['public_feedback']['status']=='PUBLIC_PASS':
   res=dict(status='PUBLIC_ACCEPTED',selected=dict(code=ev['candidate_code']),last_candidate=ev['candidate_code'],events=[],hook_events=[],budget=b.snapshot(),not_routed='already PUBLIC_PASS; zero solve calls; not an operator repair')
   if plugin:plugin.finish(time.time())
  else:res=ctrl._solve(PublicTaskView.project(ev['task_public']),b,[],ev['candidate_code'],restore_feedback(ev['public_feedback']),None,plugin)
  after=r.budgets['solve'].snapshot();res.update(wall_seconds=time.monotonic()-start,tool_calls=after['tool_calls']-before['tool_calls']);results[arm]=res;write(folder/'reuse'/f'{arm}_workflow.json',res);r.save();print('REUSE',card.operator_id,arm,res['status'],b.calls,flush=True)
  if any(x['status']=='UNKNOWN' for t in r.transports.values() for x in t.audit):raise RuntimeError('unknown request stops run')
 # Only now open external check channel; never pass these to a model or retry.
 for arm,res in results.items():
  code=res['selected']['code'] if res['selected'] else res['last_candidate'];res['external_review']=r.judge.run(tid,code,item['external_cases']);write(folder/'external_governance'/f'reuse_{arm}.json',res['external_review'])
 f=results['F'];applied=any(x['status']=='applied' for x in f.get('hook_events',[]))
 if applied and not f['external_review']['passed']:r.registry.suspend(card,'EXTERNAL_GOVERNANCE: reuse program fails frozen statement-domain audit; not online-discovered feedback',time.time())
 return results

def run():
 items=base_inputs();files=[Path(__file__),ROOT/'scripts/run_workflow_v2.py',ROOT/'scripts/experiment_s16b2_source.py',e.prior.old.WORKER,e.prior.old.ACCEPTANCE]+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
 for item in items.values():files += [ROOT/item['lineage']['raw_path'],Path(item['task']['reference_path'])]
 plan=dict(run_id=OUT.name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='real_experiment',frozen_files={str(p.relative_to(ROOT)):sha(p) for p in files},budgets={'learning':e.prior.config(4,0,500000,65536),'solve':e.prior.config(20,600,1850000,65536)},per_task=dict(max_calls=2,max_tokens=147456,max_tools=40,wall_seconds=240),families=FAMILIES,inputs_hash=fingerprint(items),common_delivery=COMMON,memory_rule='Verbatim model-generated repair_strategy <=1500 UTF8 bytes; if longer, use first complete sentences within bound and log removed length. Not a separately learned online memory.',hard_budget_usd=2.4,max_learning_calls=6,max_source_calls=8,max_reuse_calls=12,model_limits=dict(input_upper=65536,output=8192,thinking='disabled',temperature=0),external_feedback='Governance only; never part of spec/candidate/revision/memory/controller inputs; no revisions after external evaluation.',stopping='Max one source candidate plus one public/static revision per family; external source failure suspends and skips reuse; unsuccessful sources stay Shadow; no replacement mechanisms, promotion or streams.',authorization='User requests S16-E1/E2/E3. Exactly two selected real public failure categories; <=26 calls and $2.40 fresh total cap.',price=dict(input_miss=.3,output=1.2,per='million Tokens',source='https://api-docs.deepseek.com/quick_start/pricing/',checked='2026-10-22'),local_currency_cost=None)
 plan['protocol_hash']=fingerprint(plan)
 os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
 r=e.ExperimentRunner(OUT,plan,sender_factory);(OUT/'tmp').mkdir();tempfile.tempdir=str(OUT/'tmp');write(OUT/'authorization.json',dict(run_id=OUT.name,protocol_hash=plan['protocol_hash'],budgets=plan['budgets'],allow_real_api=True,basis=plan['authorization']));write(OUT/'frozen_inputs_external_separate.json',items)
 history={str(p):sha(p) for d in [ROOT/'runs/s16b2_normalized_spec_20261022_01',ROOT/'runs/s16c_reuse_20261022_02',ROOT/'runs/s16c2_reuse_20261022_01'] for p in d.rglob('*') if p.is_file()};write(OUT/'historical_before.json',history)
 outcomes={};cards=[];error=None
 try:
  # E1: zero model requests, real reproduction and scorer acceptance before any learning.
  for tid,item in items.items():
   task=item['task'];ref=Path(task['reference_path']).read_text();checks=dict(reference_public=r.judge.run(tid,ref,task['public_cases']),reference_external=r.judge.run(tid,ref,item['external_cases']),failure_public=r.judge.run(tid,item['code'],task['public_cases']),invalid=r.judge.run(tid,"print('INVALID')",task['public_cases']))
   write(OUT/'E1'/f'{tid}_verification.json',checks);assert checks['reference_public']['passed'] and checks['reference_external']['passed'] and not checks['invalid']['passed']
   item['packet']=public_packet(task,item['code'],checks['failure_public'],item['finish']);write(OUT/'public_packets'/f'{tid}.json',item['packet'])
  write(OUT/'E1/attribution.json',dict(new_api_calls=0,v0_status='suspended unchanged',observations=['C2 F public3/3 but external12/18; short output was incorrect, not an effective saving','C2 M17/18, G two length outputs; no causal attribution to policy','external audit is experiment governance; online agent saw only PUBLIC_PASS'],changes=['same stronger concise complete-code instruction in G/M/F','public learning and external governance saved separately','new categories: executable wrong answer and runtime-failing fragment; old v0 not edited']))
  for fam in FAMILIES:
   key=fam['key'];src=items[fam['source'][0]];future=items[fam['reuse'][0]];folder=OUT/key;folder.mkdir();outcomes[key]=dict(status='STARTED',source=fam['source'][0],reuse=fam['reuse'][0],versions=[]);packet=src['packet']
   if packet['public_feedback']['status']!=fam['status']:
    outcomes[key]['status']='NO_REPROJECTED_SOURCE_FAILURE';continue
   specprompt='Induce a reusable workflow mechanism from ONLY the actual public failure below. Do not solve the problem, assert certified root cause, or assume an absent/full algorithm without checking the provided code. All arms already request concise complete programs. Return exactly mechanism,conditions,repair_strategy,refusal_conditions,stop_rule,limitations as nonempty strings. Keep repair_strategy <=1500 UTF8 bytes for a fair verbatim text-experience comparator. No task IDs or hardcoded source constraints.\n'+canonical(packet)
   try:
    response=send_learning(r,key+'/spec',[dict(role='system',content='Induce a specification as JSON; public data only.'),dict(role='user',content=specprompt)]);normalized=normalize(response);normalized['normalization']['origin']='new_real_public_induction';spec=normalized['specification'];write(folder/'specification.json',normalized)
   except ValueError as exc:outcomes[key]['status']='SPEC_CONTRACT_FAILED';outcomes[key]['error']=str(exc);continue
   memory=spec['repair_strategy'];parts=memory.split('. ');kept=[]
   for part in parts:
    trial='. '.join(kept+[part])
    if len(trial.encode())>1500:break
    kept.append(part)
   memory='. '.join(kept);assert memory,'no complete bounded memory';write(folder/'M_memory.json',dict(memory=memory,source='verbatim repair_strategy complete-sentence prefix',original_bytes=len(spec['repair_strategy'].encode()),kept_bytes=len(memory.encode())))
   now=time.time();event=r.stores['F'].record(stream_id=OUT.name+'-development',task_id=src['task']['task_id'],family_id=key,stage='l1',code=packet['candidate_code'],feedback=restore_feedback(packet['public_feedback']),observed_at=now,available_from=now,finish_reason=src['finish'],provenance_group_id=src['task']['task_id'],synthetic=False);write(folder/'source_event.json',event)
   prior=None;diagnosis=None;winner=None
   for rev in range(2):
    vf=folder/f'v{rev}';vf.mkdir();response=send_learning(r,key+f'/candidate-r{rev}',learn_messages(spec,packet,prior,diagnosis));write(vf/'raw_compile.json',response);prior=response['text']
    try:
     artifact=e.prior.json_response(response);assert set(artifact)=={'code','description','applicability'} and all(isinstance(v,str) and v.strip() for v in artifact.values());write(vf/'artifact.json',artifact);(vf/'operator.py').write_text(artifact['code']);static=validate_source(artifact['code'])
    except (ValueError,AssertionError) as exc:static=dict(passed=False,error='COMPILE_OUTPUT_CONTRACT_ERROR '+str(exc))
    write(vf/'static.json',static);diagnosis=static;outcomes[key]['versions'].append(dict(version=rev,static=static))
    if not static['passed']:continue
    card=WorkflowPolicy(key,f'v{rev}',str(vf/'operator.py'),sha(vf/'operator.py'),r.context,'Source-effective only; one preregistered future public-failure task', (event['event_id'],),(src['task']['task_id'],),allowed_feedback=(fam['status'],),structural_statuses=('STRUCTURAL_PASS',),source_mode='chronological_simulation')
    r.registry.register(card,time.time());cards.append(card);functional=validate(r,card,src,vf);diagnosis=functional;outcomes[key]['versions'][-1]['source_pass']=functional['passed']
    if functional['passed']:winner=(card,vf,functional);break
   if not winner:outcomes[key]['status']='NO_SOURCE_EFFECT_SHADOW';continue
   card,vf,functional=winner;admit(r,card,event,vf,future['task']['task_id']);outcomes[key]['status']='SOURCE_EFFECTIVE_NURSERY';outcomes[key]['winner']=card.to_dict()
   # Source final audit is opened only after version selection and admission, with NO revision.
   j=len(functional['trials'])-1;code=read(vf/f'source_response_{j}.json')['code'];external=r.judge.run(src['task']['task_id'],code,src['external_cases']);write(vf/'external_governance/source.json',external);outcomes[key]['source_external']=dict(passed=external['passed'],tests_run=external['tests_run'],tests_passed=external['tests_passed'])
   if not external['passed']:
    r.registry.suspend(card,'EXTERNAL_GOVERNANCE: source selected program fails external checks; no feedback to learner',time.time());outcomes[key]['status']='SOURCE_EXTERNAL_FAILED_SUSPENDED';continue
   result=reuse(r,card,future,memory,vf);outcomes[key]['reuse_results']={a:dict(public_pass=z['status']=='PUBLIC_ACCEPTED',external_pass=z['external_review']['passed'],external_tests_passed=z['external_review']['tests_passed'],external_tests_run=z['external_review']['tests_run'],budget=z['budget'],operator_applied=any(h['status']=='applied' for h in z.get('hook_events',[])),wall_seconds=z['wall_seconds'],tool_calls=z['tool_calls']) for a,z in result.items()};outcomes[key]['status']='REUSE_COMPLETED'
 except Exception as exc:error=dict(type=type(exc).__name__,message=str(exc));print('STOPPED',error,flush=True)
 finally:
  r.save();rows=[x for t in r.transports.values() for x in t.audit if x.get('raw_response')];write(OUT/'summary.json',dict(error=error,outcomes=outcomes,cards=[dict(card=c.to_dict(),review=r.registry.review(c)) for c in cards],actual_responses=len(rows),tokens=sum(x['raw_response']['usage']['total_tokens'] for x in rows),estimated_usd=sum((x['raw_response']['usage']['prompt_tokens']*.3+x['raw_response']['usage']['completion_tokens']*1.2)/1e6 for x in rows),budgets={k:b.snapshot() for k,b in r.budgets.items()},historical_changed=[p for p,h in history.items() if sha(p)!=h]));print('FINISHED',json.dumps({k:v['status'] for k,v in outcomes.items()}),flush=True)
 if error:raise RuntimeError('run stopped; no automatic retry')
if __name__=='__main__':run()
