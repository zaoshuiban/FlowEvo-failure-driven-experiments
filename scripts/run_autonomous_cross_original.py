"""Bounded cross-original discovery and paired development replication.
No target material enters generation; no new algorithm is implemented in host.
"""
import argparse,copy,json,hashlib,time,tempfile,sys,subprocess
from pathlib import Path
import run_autonomous_v2_deepseek as base
from run_autonomous_v2_deepseek import (ROOT,OLD,IMAGE,WORKER,sha,validator,
    FailureEvidenceStore,EvidenceStore,TrustedLearningEvidence,CompileQueue,
    LearningLoop,SymptomLearning,DeepSeekMechanismConfig,DeepSeekMechanismAdapter,
    BoundedCompiler,PersistentBudget,Budget,FrozenLinuxBackend,FailureOperatorRegistry,
    Fingerprint,ExecutableLearningPipeline,canonical,fingerprint,VERSION)
from failure_evo.contracts import PublicTaskView,PublicFeedback
from failure_evo.workflow_protocol_v2 import SharedTransport,repair_messages,prepare as wire_prepare,delivery,Limits
from failure_evo.model_api import DeepSeekGenerator,configured_api_key
RUN=ROOT/'runs/autonomous_cross_original_20261027_01'
base.RUN=RUN
save=base.save

def read(p):return json.loads(Path(p).read_text())

def prepare_run():
 RUN.mkdir(exist_ok=True);(RUN/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(RUN/'tmp')
 selections=[('01','runs/s20_taco80_m_20261025_01/evidence_M.jsonl'),('04','runs/s19_stream20_20261024_01/evidence_F.jsonl')]
 facts=[];checkpoints={};stores=[];historical={};selection=[]
 for pos,path in selections:
  packet_path=ROOT/f'reports/s22_action_preference_v1/frozen/{pos}.json'
  packet=read(packet_path)['public_checkpoint'];store=FailureEvidenceStore(ROOT/path);stores.append(store)
  fact=next(f for f in store.visible(time.time()) if f['event_id']==packet['event_id'])
  assert sha(store.artifacts/(fact['candidate_sha256']+'.py'))==fact['candidate_sha256']
  task=copy.deepcopy(packet['task_public'])
  task['public_examples']=[dict(input=c['input'],expected=c['expected'],visibility='public',legal_verified=True) for c in packet['public_cases']]
  feedback=dict(status=packet['feedback']['status'],summary=packet['feedback']['summary'],visibility='public',cases=[dict(c,visibility='public',legal_verified=True) for c in packet['feedback']['public_cases']])
  cp=dict(event_id=fact['event_id'],task=task,code=packet['code'],feedback=feedback,observed_at=fact['observed_at'],lineage_id=fact['provenance_group_id'])
  # Rebind to the original earliest source for 91, not later S22 outcome summaries.
  if pos=='04':
   prior=read(ROOT/'reports/autonomous_mvp_v1/historical_replay_accepted/discovery_job.json')['discovery']['evidence'][0]
   cp['task']=dict(prior['task'],public_examples=[dict(c,visibility='public',legal_verified=True) for c in prior['task']['public_examples']])
   cases=[json.loads(c) if isinstance(c,str) else c for c in prior['feedback']['public_cases']]
   cp['feedback']=dict(status=prior['feedback']['status'],summary=prior['feedback']['summary'],visibility='public',cases=[dict(c,visibility='public',legal_verified=True) for c in cases])
   assert cp['code']==prior['code']
  facts.append(fact);checkpoints[fact['event_id']]=cp
  selection.append(dict(position=pos,task_id=fact['task_id'],event_id=fact['event_id'],historical_stream=fact['stream_id'],available_from=fact['available_from']))
  historical[path]=sha(ROOT/path);historical[str(packet_path.relative_to(ROOT))]=sha(packet_path)
 class Selected:
  def __init__(self):
   self.events=EvidenceStore(RUN/'discovery_projection.jsonl');self.artifacts=RUN/'bound_original_programs';self.artifacts.mkdir(exist_ok=True)
   for f,cp in zip(facts,checkpoints.values()):
    path=self.artifacts/(f['candidate_sha256']+'.py');data=cp['code']
    assert hashlib.sha256(data.encode()).hexdigest()==f['candidate_sha256']
    if path.exists():assert path.read_text()==data
    else:path.write_text(data)
  def visible(self,at,stream_id=None):
   if stream_id not in (None,RUN.name):return ()
   return tuple(f for f in facts if f['available_from']<=at)
 store=Selected();old=read(OLD)
 targets=old['groups']['independent']
 controls=[c for c in old['groups']['negative'] if c['task']['problem_id'].endswith('r1248')]
 vals={c['task']['problem_id']:validator(c['task']) for c in targets+controls}
 vals.update({cp['task']['problem_id']:validator(cp['task']) for cp in checkpoints.values()})
 for c in targets+controls:
  assert all(vals[c['task']['problem_id']].verify(c['task'],x['input'])['valid'] for x in c['task']['public_examples'])
 cutoff=max(f['available_from'] for f in facts)
 # This is a frozen discovery batch of different symptoms, not an asserted family.
 job=dict(job_id=fingerprint([RUN.name,[f['event_id'] for f in facts]]),stream_id=RUN.name,
   family_id=fingerprint(['unverified-discovery-batch',[f['family_id'] for f in facts]]),
   evidence_ids=[f['event_id'] for f in facts],completed_tasks=2)
 loop=LearningLoop(CompileQueue(RUN/'queue.jsonl'),store,RUN.name,RUN/'loop.jsonl')
 admission=TrustedLearningEvidence(store,RUN/'admission.jsonl',vals)
 public=admission.build(loop.public_input(job,cutoff),checkpoints,at=cutoff)
 # Index original distinct symptoms; do not imply a common mechanism from a batch.
 index=SymptomLearning(RUN/'symptoms.jsonl',store,RUN.name)
 for f in facts:
  cp=checkpoints[f['event_id']]
  index.ingest(f,PublicFeedback.project(cp['feedback']),cp['code'],remaining_calls=1,at=cutoff)
 if not loop.queue.events.records():loop.queue.events.append('DISCOVERY_BATCH_FROZEN',dict(job,shared_root_cause='UNVERIFIED',selection='fixed public-data order, no outcome selection'),time.time())
 save('public_job.json',public);save('targets.json',targets);save('negative_controls.json',controls)
 assert {c['task']['problem_id'] for c in targets+controls}.isdisjoint({f['task_id'] for f in facts})
 assert {c['lineage_id'] for c in targets+controls}.isdisjoint({f['provenance_group_id'] for f in facts})
 assert {hashlib.sha256(c['code'].encode()).hexdigest() for c in targets+controls}.isdisjoint({f['candidate_sha256'] for f in facts})
 save('selection.json',dict(sources=selection,targets=[c['task']['problem_id'] for c in targets],negative=[c['task']['problem_id'] for c in controls],
  rule='Sources: first two S22 frozen-order entries with a reviewed legal public projection and no image/known-illegal input (01,04). Targets: existing first-two complete non-image repair-target order (06,07); no outcome-dependent replacement.',
  other_entries='02 image; 03 previously identified illegal sample; 05 syntax-invalid; 08 negative reference control after legal-input exclusions; no new scan of 800 tasks',
  development_exposed=True,targets_withheld_from_this_generation=True,prior_target_control_results_known=True,
  same_original_reuse_insufficient=True,lineage_proxy_only=True,confirmation119_used=False,external419_used=False))
 # Retain the audited original-URL/statement/code proxies from preparation.
 prep=OLD.parent
 for name in ('lineage_audit.json','selection.json'):
  if (prep/name).exists():save('prior_'+name,read(prep/name))
 metadata=read(ROOT/'runs/autonomous_v2_deepseek_source_20261027_01/model_metadata.json')
 cfg=DeepSeekMechanismConfig('deepseek-flash',metadata['official_version'],300000,1200000,metadata['source'],'2026-10-27')
 save('model_metadata.json',metadata)
 manifest=read(ROOT/'reports/s22_action_preference_v1/scoring_manifest.json')
 reviews=[r for r in manifest['rows'] if r['task_id'] in {c['task']['problem_id'] for c in targets}]
 save('final_review_descriptors.json',reviews)
 dependencies=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__),ROOT/'scripts/run_autonomous_v2_deepseek.py',ROOT/'scripts/prepare_autonomous_pilot.py',ROOT/'scripts/s24_input_legality.py',WORKER]
 p=dict(run_id=RUN.name,protocol='autonomous-cross-original-v1',generator_protocol=VERSION,
  git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  selection_sha256=fingerprint(read(RUN/'selection.json')),source_sha256=fingerprint(public),targets_sha256=fingerprint(targets),negative_sha256=fingerprint(controls),
  model=metadata,temperature=0,thinking='disabled',output_tokens=8192,generation_input_upper=65536,solve_input_upper=32768,
  generation_calls=3,paired_solver_calls=4,max_total_calls=7,max_cost_microusd=500000,
  user_authorization='User authorizes real experiment, changed generator to DeepSeek and requires different-original reuse; existing spending authorization persists',
  stages=['one induction','if PROPOSE one candidate','one source-only diagnostic revision if needed','freeze winner','negative check','two cross-original G/F pairs','lock all online outputs','same-task final review'],
  source_gate='at least one source truly repaired, no observed source regression, static and safety pass; other source may decline; this is offline Shadow testing, not Experimental promotion',
  target_selection='frozen before new model outputs; no replacement; source/target code and original IDs disjoint',
  target_feedback_to_generator=False,reference_solutions_to_generator=False,old_generated_operators_to_generator=False,
  pair_order=[['G','F'],['F','G']],branch_model_call_limit=1,
  fallback='F failed/declined: same frozen Generic repair of original checkpoint, one call total, never attribute fallback success to operator',
  success='operator applied and both public and final review passed on a different original; advantage requires F-only correct OR equally correct with fewer online model resources; report build costs separately and cumulatively',
  permission_ceiling='shadow offline explicitly authorized research validation',statistical_scope='2 exposed development targets, single draws; no population or causal significance claim',
  stops=['NO_MECHANISM','HYPOTHESIS_ONLY','invalid contract','source gate fails after one revision','negative regression','UNKNOWN request','Worker infrastructure failure','budget exhausted'],
  dependencies={str(f.relative_to(ROOT)):sha(f) for f in dependencies},historical_inputs=historical,
  worker=dict(image=IMAGE,script_sha256=sha(WORKER)),final_review_sources={r['evaluator_ref']:manifest['evaluator_sources'][r['evaluator_ref']] for r in reviews})
 save('protocol.json',p)
 a=DeepSeekMechanismAdapter(RUN/'preflight_provider.jsonl',Budget(),config=cfg,mock=True,sender=lambda _:None,max_wire_input_upper=65536)
 wire=a.preflight(dict(public,phase='induction',slot=0,max_tokens=8192));save('frozen_induction_wire.json',wire)
 # G/fallback wire is frozen without reading final review answers.
 for i,c in enumerate(targets):
  packet=read(ROOT/f'reports/s22_action_preference_v1/frozen/{i+6:02}.json')['public_checkpoint']
  assert packet['code']==c['code']
  messages,_=repair_messages(c['task'],'```python\n'+c['code']+'\n```',packet['feedback'])
  prepared=wire_prepare(messages)
  save(f'generic_wire_{i}.json',dict(body=prepared.body,sha256=prepared.sha256,measures=prepared.measures))
 save('preflight.json',dict(protocol_sha256=fingerprint(p),generation_wire_sha256=fingerprint(wire),wire_input_upper=len(canonical(wire).encode())+256,new_model_calls=0,source_tasks=2,target_tasks=2))
 return p,public,cfg,store,loop,vals,targets,controls

def budget(p):
 return PersistentBudget(RUN/'budget.jsonl',run_id=RUN.name,protocol_hash=fingerprint(p),max_calls=7,max_tokens=516096,max_tools=160,
  max_cost_microusd=p['max_cost_microusd'],token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,
  max_tool_milliseconds=19200000,tool_milliseconds_upper=120000,wall_seconds=5400)

def pairs(pipe,card,targets,b,p):
 rows=[];audit=[]
 def sender(w):
  key=fingerprint(w.decode());save('solve_sends/'+key+'.json',dict(state='SEND_STARTED',wire_sha256=key))
  raw=DeepSeekGenerator._post(json.loads(w),configured_api_key(),240)
  save('solve_responses/'+key+'-'+str(len(audit))+'.json',raw);return raw
 tr=SharedTransport(b,sender,authorized=dict(run_id=RUN.name,protocol_hash=fingerprint(p)),audit=audit)
 for i,c in enumerate(targets):
  arms={}
  for arm in p['pair_order'][i]:
   op=pipe._cases(card,[dict(c,expectation='repair')])[0] if arm=='F' else None
   if op and op['passed']:
    code=op['operator_result']['candidate_code'];public=op['after'];response=None
   else:
    w=read(RUN/f'generic_wire_{i}.json')['body'];prepared=wire_prepare(w['messages'])
    response=tr.send(prepared,request_id=f'{RUN.name}/{i}/{arm}',capability='paired-generic-repair')
    code=delivery(response['text'],response['finish_reason'])['code']
    public=pipe._engine._tool('paired_public',lambda:pipe.evaluator(PublicTaskView.project(c['task']),code))
   arms[arm]=dict(code=code,public=public,response=response,operator=op,operator_success=bool(op and op['source_effective']),fallback=bool(op and not op['passed']))
   save(f'pairs/{i}_{arm}.json',arms[arm]);save(f'solve_audit_{i}_{arm}.json',audit)
  rows.append(dict(task_id=c['task']['problem_id'],arms=arms))
 save('online_locked.json',dict(rows_sha256=fingerprint(rows),at=time.time()))
 # The old development review corpus is deliberately opened only after lock.
 descriptors={r['task_id']:r for r in read(RUN/'final_review_descriptors.json')}
 for row,c in zip(rows,targets):
  ref=descriptors[row['task_id']]['evaluator_ref'];assert sha(ROOT/ref)==p['final_review_sources'][ref]
  raw=read(ROOT/ref)
  if isinstance(raw,dict):cases=raw[row['task_id']]['audit_cases']
  else:cases=next(x for x in raw if x['task_id']==row['task_id'])['cases']
  cases=[dict(input=x['input'],expected=x.get('expected',x.get('output')),visibility='public',legal_verified=True) for x in cases]
  task=dict(c['task'],public_examples=cases)
  assert all(validator(task).verify(task,x['input'])['valid'] for x in cases)
  for arm,a in row['arms'].items():
   a['final_review']=pipe._engine._tool('offline_final_review',lambda:pipe.evaluator(PublicTaskView.project(task),a['code']))
   a['joint_pass']=a['public']['status']=='PUBLIC_PASS' and a['final_review']['status']=='PUBLIC_PASS'
 save('paired_results.json',rows)
 return rows

def execute():
 p,job,cfg,store,loop,vals,targets,controls=prepare_run()
 if (RUN/'execution_started.json').exists():raise ValueError('consumed Run; no resend')
 save('execution_started.json',dict(protocol_sha256=fingerprint(p),at=time.time()))
 b=budget(p);auth=dict(run_id=RUN.name,protocol_hash=fingerprint(p),model=cfg.model,protocol=VERSION,max_cost_microusd=p['max_cost_microusd'],paid_api_authorized=True)
 save('authorization.json',auth)
 adapter=DeepSeekMechanismAdapter(RUN/'provider.jsonl',b,config=cfg,authorization=auth,max_wire_input_upper=65536)
 compiler=BoundedCompiler(adapter,b,RUN/'compiler.jsonl',cfg.model,max_input_upper=65536,max_output_upper=8192)
 backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER);registry=FailureOperatorRegistry(RUN/'registry.jsonl',store)
 ctx=Fingerprint('native-five-stage','public-stdio-tokens-v1','deepseek-flash',fingerprint(p['dependencies']),VERSION)
 pipe=ExecutableLearningPipeline(RUN/'pipeline',compiler,b,registry,ctx,backend,input_validators=vals)
 pipe.job=job;pipe.at=time.time();pipe.manifest={'discovery':{'source_groups':[e['lineage_id'] for e in job['discovery']['evidence']]},'design':{'source_groups':[]}}
 pipe.sources=[dict(case_id=e['event_id'],task=dict(e['task'],public_examples=[dict(c,visibility='public',legal_verified=True) for c in e['task']['public_examples']]),code=e['code'],lineage_id=e['lineage_id'],expectation='repair') for e in job['discovery']['evidence']]
 status='STARTING';reviews=[];paired=[]
 try:
  baselines=[]
  for c in pipe.sources:
   result=pipe._engine._tool('source_baseline_preflight',lambda:pipe.evaluator(PublicTaskView.project(c['task']),c['code']))
   baselines.append(result)
   if result['status'] in ('PUBLIC_PASS','EVALUATOR_ERROR'):raise RuntimeError('source no longer a credible failure')
  save('baselines.json',baselines)
  spec=compiler.request(job,'induction',0,time.time(),output_upper=8192);h=pipe._hypothesis(spec['specification'],job)
  if h['decision']!='PROPOSE':status=h['decision']
  else:
   payload=dict(job,specification=spec['specification'])
   for version in range(2):
    resp=compiler.request(payload,'candidate' if version==0 else 'revision',0,time.time(),output_upper=8192)
    review=pipe._design(resp['code'],{'cases':[]},b.remaining_seconds);reviews.append(review);save(f'source_review_v{version}.json',review)
    source_ok=review['static']['static_pass'] and any(r['source_effective'] for r in review['source']) and not any(r['regressed'] for r in review['source'])
    if source_ok:
     card=pipe._card(resp['code']);save('winner_locked.json',dict(artifact_sha256=card.artifact_sha256,version=version,at=time.time(),target_feedback_seen=False))
     negatives=pipe._cases(card,[dict(c,expectation='decline') for c in controls]);save('negative_validation.json',negatives)
     if not all(r['eligible'] for r in negatives):status='NEGATIVE_GATE_FAILED';break
     paired=pairs(pipe,card,targets,b,p)
     reuse=[r['task_id'] for r in paired if r['arms']['F']['operator_success'] and r['arms']['F']['joint_pass']]
     status='CROSS_ORIGINAL_REUSE_OBSERVED' if reuse else 'NO_CROSS_ORIGINAL_REUSE'
     break
    status='NO_SOURCE_EFFECT_AFTER_BOUNDED_ATTEMPT'
    if version==0:payload=dict(payload,code=resp['code'],design_feedback=dict(static=review['static'],source=review['source']))
  save('result.json',dict(status=status,versions=len(reviews),cross_original_pairs=len(paired),experimental=0,budget=b.snapshot(),not_independent_confirmation=True))
 except BaseException as exc:
  save('stopped.json',dict(status='STOPPED',error=type(exc).__name__,reason=str(exc),budget=b.snapshot()));raise
 finally:
  loop.queue.events.append('COMPILE_ATTEMPTED',{k:job[k] for k in ('job_id','stream_id','family_id','evidence_ids','completed_tasks')},time.time())
  save('historical_integrity_after.json',{f:sha(ROOT/f)==h for f,h in p['historical_inputs'].items()})
 print(status,flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--execute-authorized',action='store_true');args=parser.parse_args()
 if args.execute_authorized:execute()
 else:
  p,*_=prepare_run();print('ZERO_API_FROZEN',fingerprint(p))
