"""S22 bounded repository census. Real public evidence; no model/Worker sends."""
import collections,hashlib,json,pathlib,re,sys
from s22_ab import ROOT,freeze,classify
from failure_evo.contracts import atomic_json,fingerprint
from failure_evo.learning_evidence_bundle import check_packet,checkpoint_budget
from failure_evo.repair_choice_v2 import observation,eligible_actions
from failure_evo.selective_experience import STAGES
OUT=ROOT/'reports/s22_action_preference_v1'
FILES={}
def read(p):
 p=pathlib.Path(p);p=p if p.is_absolute() else ROOT/p
 FILES[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
def counts(values):return dict(sorted(collections.Counter(values).items()))
def dataset(t):
 return 'TACO' if 'taco' in t.lower() else 'LiveCodeBench' if any(s in t.lower() for s in ['lcb','atcoder']) else 'APPS' if 'apps' in t.lower() else 'CodeContests' if 'contests' in t.lower() else 'UNKNOWN'
def phash(p):return hashlib.sha256(' '.join(p['task_public']['prompt'].split()).encode()).hexdigest()

def pairs_audit():
 pairs=[]
 for run,pre in [('s17b_pairs_20261023_01','s17b_decision_space_20261023_01'),('s18p2_pairs_20261023_01','s18p2_preparation_20261023_01')]:
  summary=read(ROOT/'runs'/run/'summary.json');plan=read(ROOT/'runs'/pre/'paired_plan.json')
  for task in plan['selected']:
   base=ROOT/'runs'/pre/'frozen'/task;checkpoint=read(base/'checkpoint.json')
   code=checkpoint['candidate_code'];feedback=checkpoint['public_feedback'];arms={}
   for arm,action in [('A','REPAIR_EXISTING'),('B','REGENERATE_FRESH')]:
    req=read(base/(action+'.json'));result=read(ROOT/'runs'/run/'branches'/task/arm/'result.json');stats=summary['arms'][task+'/'+arm]
    steps=result.get('steps',[]);first=steps[0] if steps else None
    reqhash=fingerprint(req)
    request_context=json.loads(req['messages'][1]['content'].rsplit('\n',1)[-1])
    arms[arm]=dict(model=req['model'],temperature=req.get('temperature'),thinking=req.get('thinking'),max_tokens=req['max_tokens'],wire_sha256=reqhash,initial_request_bound=bool(first and first['request_sha256']==reqhash),response_models=sorted({step['response']['model'] for step in steps}),finish_reasons=[step['response']['finish_reason'] for step in steps],initial_public_counts=[first['public']['tests_passed'],first['public']['tests_run']] if first else None,initial_public_pass=first['public']['passed'] if first else None,final_public_pass=stats['public_pass'],review_passed=stats.get('review_passed'),review_total=stats.get('review_total'),strict_pass=False if stats['public_pass'] is False else stats['review_passed']==stats['review_total'] if stats.get('review_total') else None,calls=stats['calls'],input_tokens=stats['input_tokens'],output_tokens=stats['output_tokens'],reasoning_tokens=[x['response']['usage'].get('completion_tokens_details',{}).get('reasoning_tokens') for x in steps],estimated_usd=stats['estimated_usd'],blocked=stats['blocked'],unknown_requests=summary['budget']['unknown_or_pending_requests'],source_present=request_context.get('candidate_code')==code,public_feedback_keys=sorted(request_context['public_feedback']),feedback_actual_visible=any('actual' in c for c in request_context['public_feedback'].get('public_cases',[])),request_metadata=req)
   samecfg=all(arms['A'][k]==arms['B'][k] for k in ['model','temperature','thinking','max_tokens'])
   pairs.append(dict(run=run,task_id=task,dataset=dataset(task),checkpoint_ref=str((base/'checkpoint.json').relative_to(ROOT)),checkpoint_hash=fingerprint(checkpoint),candidate_sha256=hashlib.sha256(code.encode()).hexdigest(),feedback_hash=fingerprint(feedback),pre_failure_type=feedback['status'],stage=checkpoint.get('stage'),original_trace=checkpoint.get('source') or checkpoint.get('provenance',{}).get('workflow'),same_host_start=True,initial_wire_binding=all(x['initial_request_bound'] for x in arms.values()),same_model_settings=samecfg,per_branch_max_calls=plan.get('calls_per_branch',plan.get('requests',{}).get('per_branch')),arms=arms,initial_public_class=classify(arms['A']['initial_public_pass'],arms['B']['initial_public_pass']),final_public_class=classify(arms['A']['final_public_pass'],arms['B']['final_public_pass']),strict_complete_branch_class=classify(arms['A']['strict_pass'],arms['B']['strict_pass']),strict_one_call_class='UNKNOWN_NOT_SCORED_FOR_BOTH_INITIAL_ARTIFACTS',context_difference='B removes original code AND actual/exception public feedback; A/B instruction differs',evidence='EXPLORATORY_NOT_S22_MATCHED_LABEL'))
 return pairs

def main():
 pairs=pairs_audit();records=[];packets={};exclusions=[]
 metadata={}
 for name in ['runs/s20_preparation_20261025_01/task_lineage_manifest.json','runs/s19g_train_expansion_20261024_01/task_lineage_manifest.json','runs/s18_observe_20261023_01/observation_tasks.json','runs/s13_compare30_20261022_01/tasks.json']:
  for row in read(name):
   m={k:row.get(k) for k in ['difficulty','original_url','original_id']}
   if row.get('task_public'):m['question_hash']=phash(row)
   metadata.setdefault(row['task_id'],{}).update({k:v for k,v in m.items() if v is not None})
 # Full top-level real FailureEvidenceStore census; nested fixtures/replays aren't fresh runs.
 for path in sorted([*(ROOT/'runs').glob('*/evidence_*.jsonl'),ROOT/'runs/s13_compare30_20261022_01/failure_evidence.jsonl']):
  FILES[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();run=path.parent;arm='FailureLearning' if path.name=='failure_evidence.jsonl' else path.stem.split('_')[-1]
  for line in path.read_text().splitlines():
   raw=json.loads(line)
   if raw.get('kind')!='FAILURE_FACT':continue
   f=raw['payload']
   if f.get('visibility')!='public' or f.get('synthetic') is not False:
    exclusions.append(dict(ref=str(path.relative_to(ROOT)),reason='NOT_REAL_PUBLIC_FACT'));continue
   ppath=run/'public_packets'/f"{f['event_id']}.json";p=None;reason=[]
   if ppath.exists():
    try:
     p=check_packet(read(ppath))
     assert all(p[k]==f[k] for k in ['task_id','event_id','stage','candidate_sha256'])
     packets[(run.name,arm,f['event_id'])]=p
    except Exception as exc:reason.append('INVALID_PACKET:'+str(exc));p=None
   else:reason.append('NO_RESTORABLE_PUBLIC_PACKET')
   rec=dict(run=run.name,arm=arm,event_id=f['event_id'],task_id=f['task_id'],stage=f['stage'],observed_at=f['observed_at'],source_ref=str(path.relative_to(ROOT)),packet_ref=str(ppath.relative_to(ROOT)) if p else None,candidate_sha256=f['candidate_sha256'],failure_type=f['verifier_status'],observation_type=f.get('observation_type'),dataset=dataset(f['task_id']),difficulty='UNKNOWN_NOT_IN_PUBLIC_RECORD',provenance_group=f.get('provenance_group_id'),question_hash=phash(p) if p else None,legal_both=False,reasons=reason,record_kind='REAL_FAILURE_FACT')
   if p:
    budget=checkpoint_budget(p);obs=observation(p['code'],__import__('failure_evo.contracts',fromlist=['strict_feedback']).strict_feedback(p['feedback']),budget)
    legal=eligible_actions(p['code'],__import__('failure_evo.contracts',fromlist=['strict_feedback']).strict_feedback(p['feedback']),budget)
    rec.update(observation=obs,legal_actions=list(legal),legal_both=set(legal)=={'REPAIR_EXISTING','REGENERATE_FRESH'},feedback_hash=fingerprint(p['feedback']),checkpoint_budget=p['checkpoint_budget'])
    if not rec['legal_both']:reason.append('BOTH_ACTIONS_NOT_LEGAL')
   rec['historical_pair_refs']=[x['run']+'/'+x['task_id'] for x in pairs if x['task_id']==rec['task_id'] and x['candidate_sha256']==rec['candidate_sha256']]
   records.append(rec)
 # Supplement real Controller events omitted from FailureEvidenceStore.
 existing={(x['run'],x['arm'],x['task_id'],x['stage'],x['candidate_sha256']) for x in records};workflows=0
 for planpath in sorted([*(ROOT/'runs').glob('*/plan.json'),ROOT/'runs/s13_compare30_20261022_01/protocol.json']):
  plan=read(planpath)
  if plan.get('evidence_kind')!='real_experiment' and planpath.parent.name!='s13_compare30_20261022_01':continue
  for path in sorted(planpath.parent.glob('branches/*/*/workflow.json')):
   if path.parent.name=='AFlow':continue # different controller, not a FlowEvo repair prefix
   workflows+=1;data=read(path);tid=path.parent.parent.name;arm=path.parent.name
   for e in data.get('events',[]):
    fb=e.get('public_feedback',{});status=fb.get('status')
    if status not in ('WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE','TIME_LIMIT','TIMEOUT'):continue
    code=e.get('code')
    if not isinstance(code,str):continue
    h=hashlib.sha256(code.encode()).hexdigest();key=(planpath.parent.name,arm,tid,e.get('stage'),h)
    if key in existing:continue
    existing.add(key);records.append(dict(run=key[0],arm=arm,event_id=fingerprint(key),task_id=tid,stage=e.get('stage'),candidate_sha256=h,failure_type=status,observation_type='controller_public',dataset=dataset(tid),difficulty='UNKNOWN_NOT_IN_PUBLIC_RECORD',legal_both=False,question_hash=None,observed_at=None,source_ref=str(path.relative_to(ROOT)),packet_ref=None,reasons=['NO_BOUND_FAILURE_FACT_AND_PACKET'],record_kind='REAL_CONTROLLER_PUBLIC_ONLY',historical_pair_refs=[]))
 # Conservative components: task ID, exact normalized statement or audited original URL.
 for x in records:
  m=metadata.get(x['task_id'],{});x['difficulty']=m.get('difficulty') or 'UNKNOWN_NOT_IN_PUBLIC_RECORD';x['original_url']=m.get('original_url');x['original_id']=m.get('original_id');x['question_hash']=x['question_hash'] or m.get('question_hash')
 parent={x['task_id']:x['task_id'] for x in records}
 def find(x):
  while parent[x]!=x:x=parent[x]
  return x
 hashes={}
 for x in records:
  for h in [x['question_hash'],x['original_url']]:
   if h:
    if h in hashes:parent[find(x['task_id'])]=find(hashes[h])
    else:hashes[h]=x['task_id']
 for x in records:x['task_component']=find(x['task_id'])
 candidates=[]
 for x in records:
  if not x['legal_both']:continue
  p=packets[(x['run'],x['arm'],x['event_id'])]
  prior=[(r,packets[(r['run'],r['arm'],r['event_id'])]) for r in records if r['packet_ref'] and r['run']==x['run'] and r['arm']==x['arm'] and r['task_id']==x['task_id'] and STAGES.get(r['stage'],99)<STAGES.get(x['stage'],99) and r['observed_at']<=x['observed_at']]
  history=[dict(packet=pp,observed_at=r['observed_at']) for r,pp in prior]
  try:
   frozen=freeze(p,history,x['observed_at']);x['s22_preflight']='PASS'
   x['freeze_hash']=frozen['freeze_hash'];candidates.append((x,frozen))
  except Exception as exc:x['s22_preflight']='NOT_SENT';x['reasons'].append(type(exc).__name__+':'+str(exc))
 # Earliest fully eligible prefix per original component, independent of A/B outcomes.
 first={}
 for x,f in sorted(candidates,key=lambda z:(z[0]['observed_at'],z[0]['run'],z[0]['arm'],STAGES[z[0]['stage']],z[0]['event_id'])):
  if x['task_component'] not in first:first[x['task_component']]=(x,f)
  else:x['reasons'].append('LATER_SAME_TASK_COMPONENT')
 # Freeze round-robin failure-type strata; observed-time order within each stratum.
 buckets=collections.defaultdict(list)
 for x,f in first.values():buckets[(x['dataset'],x['difficulty'],x['failure_type'])].append((x,f))
 selected=[]
 while len(selected)<10 and any(buckets.values()):
  for key in sorted(buckets):
   if buckets[key] and len(selected)<10:selected.append(buckets[key].pop(0))
 for i,(x,f) in enumerate(selected):
  x['selected_order']=i+1;atomic_json(OUT/'frozen'/f'{i+1:02d}.json',dict(public_checkpoint=packets[(x['run'],x['arm'],x['event_id'])],request_freeze=f))
 # Metadata only: no task descriptions or confirmation records.
 pool=read(ROOT/'runs/s20_external_v2_20261025_01/final_pool_statistics.json')
 learning=read(ROOT/'runs/s20_external_v2_20261025_01/learning_lineage.json')
 ids={t['id'] for t in learning};observed=ids & {x['task_id'] for x in records}
 summary=dict(real_failure_fact_records=sum(x['record_kind']=='REAL_FAILURE_FACT' for x in records),supplemental_controller_failures=sum(x['record_kind']=='REAL_CONTROLLER_PUBLIC_ONLY' for x in records),total_records=len(records),execution_failure_records=sum(x['failure_type'] in ('WRONG_ANSWER','RUNTIME_ERROR') for x in records),artifact_or_compile_records=sum(x['failure_type'] in ('NO_COMPLETE_CODE','COMPILE_ERROR') for x in records),s22_complete_pairs=0,s22_one_sided_pairs=0,s22_eligible_events_needing_two_new_calls=len(candidates),task_ids=len(parent),task_components=len({x['task_component'] for x in records}),unique_checkpoints=len({(x['task_component'],x['candidate_sha256'],x.get('feedback_hash',x['failure_type']),x['stage']) for x in records}),real_workflows_scanned=workflows,legal_both=sum(x['legal_both'] for x in records),legal_both_tasks=len({x['task_component'] for x in records if x['legal_both']}),preflight_pass=len(candidates),preflight_pass_tasks=len(first),selected_tasks=len(selected),historical_ab_pairs=len(pairs),s22_comparable_historical_pairs=0,inventory_records_linked_to_historical_pairs=sum(bool(x['historical_pair_refs']) for x in records),by_dataset=counts(x['dataset'] for x in records),by_failure_type=counts(x['failure_type'] for x in records),by_difficulty=counts(x['difficulty'] for x in records),by_run=counts(x['run'] for x in records),exclusion_reasons=counts(r for x in records for r in x['reasons']),external_learning_pool_tasks=pool['learning']['tasks'],external_learning_difficulty=pool['learning']['difficulty'],external_learning_observed_task_id_matches=len(observed),confirmation_count_metadata_only=pool['confirmation']['tasks'],new_api_calls=0)
 atomic_json(OUT/'existing_ab_audit.json',pairs);atomic_json(OUT/'checkpoint_inventory.json',dict(summary=summary,records=records,excluded=exclusions))
 atomic_json(OUT/'selected_checkpoints.json',[{k:x.get(k) for k in ('selected_order','task_id','task_component','run','arm','event_id','stage','failure_type','dataset','difficulty','packet_ref','freeze_hash')} for x,f in selected])
 atomic_json(OUT/'input_hashes.json',FILES)
 for p,h in FILES.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
 print(json.dumps(summary,indent=2));print('selected',[(x['task_id'],x['failure_type']) for x,f in selected])
if __name__=='__main__':main()
