"""Opt-in 140 Level-5 discovery tasks with bounded, preselected T/F/FC synthesis."""
import json,sys,time,re,hashlib,collections,urllib.request,concurrent.futures,subprocess
from pathlib import Path
from run_hard10_algorithm import (ROOT,WORKER,IMAGE,save,sha,load,fingerprint,canonical,Adapter,VERSION as GENERATION_VERSION,budget,PublicMathTask,NoGoldMathController,NoGoldPolicy,NoGoldSolverChannel,DiscoveryRecorder,grade_continuation,extract_answer,normalized,BoundedCompiler,component_check,FrozenLinuxBackend,EvidenceStore)
from failure_evo.workflow_protocol_v2 import PreflightRejected,prepare,Limits
from code_math.no_gold import solver_messages
OUT=ROOT/'runs/hard140_algorithm_20261028_01';VERSION='hard140-stratified-discovery-v1'
SUBJECTS=['algebra','counting_and_probability','geometry','intermediate_algebra','number_theory','prealgebra','precalculus']

def freeze():
 if (OUT/'protocol.json').exists():raise RuntimeError('already frozen')
 import pyarrow.parquet as pq
 from difflib import SequenceMatcher
 norm=lambda s:re.sub(r'\s+',' ',s).strip().lower()
 mask=lambda s:re.sub(r'\d+','N',norm(s))
 paths=list((ROOT.parent/'experiments').glob('*/data/public_tasks.jsonl'))+list((ROOT.parent/'experiments').glob('*/data/public_prompts.jsonl'))
 known=[]
 for path in paths:
  for line in path.read_text().splitlines():
   try:x=json.loads(line)
   except ValueError:continue
   for k in ['problem','prompt','question']:
    if isinstance(x.get(k),str):known.append(x[k]);break
 known += [e['task']['problem'] for e in load(ROOT/'runs/math_p2_all12_20261027_01/source_failures.json')]
 known += [x['problem'] for x in load(ROOT/'runs/hard10_algorithm_20261028_01/tasks.json')]
 for role in ['discovery','design']:
  file=ROOT/f'reports/math_no_gold_p0_20261027/data/public/{role}.jsonl'
  if file.exists():
   paths.append(file);known += [json.loads(l)['problem'] for l in file.read_text().splitlines()]
 known=list(set(known));prior=list(set(mask(s) for s in known));selected_masks=[]
 def near(s,other):
  for b in other:
   if 2*min(len(s),len(b))/(len(s)+len(b))<.9:continue
   seq=SequenceMatcher(None,s,b,autojunk=False)
   if seq.quick_ratio()>=.9 and seq.ratio()>=.9:return True
  return False
 selected={};labels=[];funnel=[];totals={}
 for sub in SUBJECTS:
  rows=pq.read_table(OUT/'private'/(sub+'.parquet')).to_pylist();order=sorted(range(len(rows)),key=lambda i:hashlib.sha256(f'hard140-v1:{sub}:{i}'.encode()).hexdigest());selected[sub]=[];totals[sub]=dict(all_rows=len(rows),level5=sum(x['level']=='Level 5' for x in rows))
  for index in order:
   x=rows[index]
   if x['level']!='Level 5':continue
   problem=x['problem'];reason=None;tid=f'hard140-math-train-{sub}-{index}';m=mask(problem)
   if '[asy]' in problem or re.search(r'(?i)\b(diagram|figure shown|shown below|pictured)\b',problem):reason='VISUAL_REQUIRED_OR_UNCERTAIN'
   elif len(problem.encode())>12000:reason='PUBLIC_INPUT_TOO_LONG'
   elif '\\boxed' not in x['solution']:reason='NO_EXPLICIT_REFERENCE_ANSWER'
   elif near(m,prior):reason='RECORDED_TEXT_NEAR_DUPLICATE'
   elif near(m,selected_masks):reason='WITHIN_POOL_NEAR_DUPLICATE'
   gold=extract_answer(x['solution'])
   if not gold:reason='EMPTY_REFERENCE'
   funnel.append(dict(task_id=tid,subject=sub,level='Level 5',reason=reason or 'SELECTED',answer_comparison_class=normalized(gold)[0]))
   if reason:continue
   selected[sub].append(dict(task_id=tid,problem=problem));selected_masks.append(m)
   labels.append(dict(task_id=tid,problem_sha256=fingerprint(problem),gold_answer=gold,reference_solution_sha256=fingerprint(x['solution']),dataset_row=index,subject=sub,level='Level 5'))
   if len(selected[sub])==20:break
  if len(selected[sub])<20:raise RuntimeError(f'Insufficient frozen-eligible {sub}: {len(selected[sub])}; no difficulty relaxation')
  print('SELECTED',sub,len(selected[sub]),flush=True)
 tasks=[selected[s][i] for i in range(20) for s in SUBJECTS];save(OUT/'tasks.json',tasks);save(OUT/'private/labels.json',labels)
 audit=dict(rule='Train; highest official Level5; SHA256 hard140-v1:subject:row order;20 per subject; seven-way interleave. No model outcomes. Symbolic references retained but unequal nonrational outputs UNVERIFIED.',known_public_texts=len(known),screened_paths=[str(p) for p in paths],funnel=funnel,totals=totals,near_duplicate='digit-masked lowercased whitespace-normalized SequenceMatcher ratio>=0.90',exposure_limit='Only recorded/public math screening; cannot rule out unrecorded semantic duplicates or model pretraining. Gate/Legacy/Fresh and external119 not accessed.');save(OUT/'selection_audit.json',audit)
 preflight=[]
 for t in tasks:
  w=prepare(solver_messages(PublicMathTask.parse(t),profile='concise-v1'),limits=Limits(input_token_upper=32768,output_tokens=8192),temperature=0);preflight.append(dict(task_id=t['task_id'],wire_sha256=w.sha256,measures=w.measures))
 save(OUT/'input_preflight.json',preflight)
 files=[Path(__file__).resolve(),ROOT/'scripts/run_hard10_algorithm.py',ROOT/'scripts/run_algorithm_evidence.py',ROOT/'scripts/run_math_v3_development.py']+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))
 p=dict(version=VERSION,at=time.time(),git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),model='deepseek-flash',solver=dict(tasks=140,calls_per_task=2,output_tokens=8192,input_upper=32768,temperature=0,profile='concise-v1',concurrency=4,dispatch='fixed consecutive windows; independent task budgets; no cross-task state; drain window on exception, stop new windows; no retry'),learning=dict(protocol=GENERATION_VERSION,arms=['T','F','FC'],max_sources_per_subject=2,max_sources=14,calls_per_arm=2,replicas=1,revisions=0,selection='After all answers locked: earliest two tasks per subject with at least one CONFIRMED_WRONG; use earliest wrong attempt only. No replacement, no later correct solution, no source hidden score to generation. Balanced arm order by chosen-source index.'),evaluation='All candidates frozen before Worker execution; source-only score. Model-generated parameter schema/mapping. No independent transfer or routing claims. No generated test used as oracle.',max_calls=364,max_cost_usd=31.5,budget_partition=dict(solver_per_task_usd=.15,generation_per_job_usd=.25,max_solver_usd=21,max_generation_usd=10.5),stops=['UNKNOWN','provider failure','worker infrastructure','source/data hash mismatch','permission/leakage','budget exhaustion'],not_sent='Review input preflight rejection records TASK_NOT_COMPLETED and continues; no retry/no feedback/no synthesis from unlocked task.',authorization='User requests100–200highest-difficulty diverse tasks and rerun; current finite140 plan; no previous-budget transfer',dataset=load(OUT/'private/dataset_revision.json'),tasks_sha256=sha(OUT/'tasks.json'),labels_sha256=sha(OUT/'private/labels.json'),selection_sha256=sha(OUT/'selection_audit.json'),raw_hashes={p.name:sha(p) for p in (OUT/'private').glob('*.parquet')},source_hashes={str(p.relative_to(ROOT)):sha(p) for p in files},previous_hashes={str(p.relative_to(ROOT)):sha(p) for name in ['hard10_algorithm_20261028_01','algorithm_evidence_20261028_01'] for p in (ROOT/'runs'/name).rglob('*') if p.is_file()},worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest())
 save(OUT/'protocol.json',p);save(OUT/'freeze.json',dict(sha256=fingerprint(p)));(OUT/'pricing.html').write_bytes(urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read())
 for rel in p['source_hashes']:
  dst=OUT/'frozen_source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/rel).read_bytes())
 print('FROZEN',fingerprint(p),flush=True)
def verify():
 p=load(OUT/'protocol.json');assert fingerprint(p)==load(OUT/'freeze.json')['sha256']
 for rel,h in p['source_hashes'].items():assert sha(ROOT/rel)==h,rel
 assert sha(OUT/'tasks.json')==p['tasks_sha256'] and sha(OUT/'private/labels.json')==p['labels_sha256'] and sha(OUT/'selection_audit.json')==p['selection_sha256'];return p

def solve_one(index,row,label,p):
 d=OUT/'solver'/row['task_id'];ph=fingerprint(p);runid=OUT.name+':'+row['task_id'];b=budget(d/'budget.jsonl',runid,ph,2,150000)
 grant=dict(run_id=runid,protocol_hash=ph,model=p['model'],max_cost_microusd=150000,paid_api_authorized=True,channel='math-solver-no-gold-v1');save(d/'authorization.json',grant)
 client=NoGoldSolverChannel(b,d/'requests.jsonl',authorization=grant);controller=NoGoldMathController(client,d/'controller.jsonl',policy=NoGoldPolicy(output_tokens=8192,delivery_profile='concise-v1'))
 recorder=DiscoveryRecorder(d/'scores.jsonl',d/'controller.jsonl',[label],grade_function=grade_continuation,scorer_version='math-p1-continuation-v1')
 try:
  task=PublicMathTask.parse(row);locked=controller.solve(task,episode_id=runid,sequence=index);score=recorder.record(task,locked);save(d/'outcome.json',score);return score
 except PreflightRejected as exc:
  save(d/'NOT_COMPLETED.json',dict(task_id=row['task_id'],reason=str(exc),request_state='NOT_SENT',no_retry=True));return dict(task_id=row['task_id'],sequence=index,final=dict(status='TASK_NOT_COMPLETED'),initial=dict(status='TASK_NOT_COMPLETED'),attempt_grades=[])

def run():
 p=verify();ph=fingerprint(p)
 if (OUT/'STARTED.json').exists():raise RuntimeError('consumed run; no implicit resume/resend')
 save(OUT/'STARTED.json',dict(at=time.time()));tasks=load(OUT/'tasks.json');labels={x['task_id']:x for x in load(OUT/'private/labels.json')};outcomes=[]
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
   for base in range(0,len(tasks),4):
    fs=[ex.submit(solve_one,i,t,labels[t['task_id']],p) for i,t in enumerate(tasks[base:base+4],start=base)];errors=[]
    for fut in fs:
     try:
      score=fut.result();outcomes.append(score);print('SOLVED',score['sequence']+1,score['task_id'],score['initial']['status'],score['final']['status'],flush=True)
     except BaseException as exc:errors.append(dict(type=type(exc).__name__,reason=str(exc)))
    save(OUT/'discovery_progress.json',outcomes)
    if errors:save(OUT/'window_errors.json',errors);raise RuntimeError('STOP_AFTER_DRAINED_WINDOW')
  evidence=[]
  for s in outcomes:
   wrong=[j for j,g in enumerate(s['attempt_grades']) if g['status']=='CONFIRMED_WRONG' and g['correct'] is False]
   if wrong:
    j=wrong[0];response=s['responses'][j];evidence.append(dict(task_id=s['task_id'],correct=False,attempt_index=j,wrong_answer=s['attempt_grades'][j]['parsed_answer'],output=response['text'],finish_reason=response['finish_reason'],locked_sha256=s['locked_sha256'],evidence_id=s['evidence_id']))
  save(OUT/'discovery_outcomes.json',outcomes);save(OUT/'failure_evidence.json',evidence)
  counts=collections.Counter();chosen=[]
  for e in evidence:
   sub=labels[e['task_id']]['subject']
   if counts[sub]<2:chosen.append(e);counts[sub]+=1
  save(OUT/'selected_failure_evidence.json',chosen);save(OUT/'DISCOVERY_COMPLETE.json',dict(at=time.time(),completed=len(outcomes),credible_failure_tasks=len(evidence),selected_for_synthesis=len(chosen)))
  print('DISCOVERY_COMPLETE',len(outcomes),len(evidence),len(chosen),flush=True)
 except BaseException as exc:save(OUT/'STOP.json',dict(at=time.time(),type=type(exc).__name__,reason=str(exc),no_resend=True,completed=len(outcomes)));raise

def generate():
 p=verify();ph=fingerprint(p)
 if not (OUT/'DISCOVERY_COMPLETE.json').exists() or (OUT/'STOP.json').exists() or (OUT/'GENERATION_STARTED.json').exists():raise RuntimeError('generation not permitted')
 save(OUT/'GENERATION_STARTED.json',dict(at=time.time()));evidence=load(OUT/'selected_failure_evidence.json');tasks={x['task_id']:x for x in load(OUT/'tasks.json')};results=[]
 try:
  for i,e in enumerate(evidence):
   arms=['T','F','FC'];arms=arms[i%3:]+arms[:i%3]
   for arm in arms:
    key=e['task_id']+'-'+arm;d=OUT/'jobs'/key;b=budget(d/'budget.jsonl',OUT.name+':'+key,ph,2,250000);grant=dict(run_id=b.config['run_id'],protocol_hash=ph,model=p['model'],protocol=GENERATION_VERSION,max_cost_microusd=250000,paid_api_authorized=True);save(d/'authorization.json',grant)
    adapter=Adapter(d/'provider.jsonl',b,model=p['model'],authorization=grant,max_wire_input_upper=65536);compiler=BoundedCompiler(adapter,b,d/'compiler.jsonl',p['model'],max_input_upper=65536,max_output_upper=8192)
    job=dict(stream_id=b.config['run_id'],family_id='hard140-source',arm=arm);save(d/'spec.json',dict(interface='solve(parameters)',schema_origin='model-proposed'));job['specification']=compiler.import_specification(job,d/'spec.json',time.time());result=dict(key=key,task_id=e['task_id'],arm=arm,status='NOT_GENERATED')
    for slot,stage in enumerate(['analysis','code']):
     inp=dict(source_tasks=[tasks[e['task_id']]])
     if stage=='analysis' and arm!='T':inp['failure_evidence']=e
     if stage=='code':inp['analysis']=analysis
     save(d/(stage+'_input.json'),inp)
     try:r=compiler.request(dict(job,stage=stage,public_input=inp),'candidate',slot,time.time(),output_upper=8192)
     except ValueError as exc:
      if any(x['kind']=='SEND_UNKNOWN' for x in adapter.events.records()):raise
      result.update(status='DELIVERY_REJECTED',stage=stage,reason=str(exc));break
     save(d/(stage+'_response.json'),r)
     if stage=='analysis':
      analysis=json.loads(r['code']);save(d/'analysis.json',analysis)
      if analysis['decision']!='PROPOSE':result['status']=analysis['decision'];break
     else:
      (d/'solve.py').write_text(r['code']);check=component_check(r['code'],'solve');save(d/'static.json',check);result.update(status='STATIC_VALID_SHADOW' if check['passed'] else 'STATIC_REJECTED',solver_sha256=sha(d/'solve.py'),errors=check['errors'])
    save(d/'result.json',result);results.append(result);print('GENERATED',key,result['status'],flush=True)
  save(OUT/'candidate_freeze.json',dict(at=time.time(),results=results,experimental=0));save(OUT/'GENERATION_COMPLETE.json',dict(at=time.time(),n=len(results)))
 except BaseException as exc:save(OUT/'STOP.json',dict(at=time.time(),stage='generation',reason=str(exc),no_resend=True,completed_candidates=results));raise

def evaluate():
 # Reuse frozen source-only evaluation, including parameter schema checks and output lock.
 import run_hard10_algorithm as old
 old.OUT=OUT;old.verify=verify;old.evaluate()
if __name__=='__main__':globals()[sys.argv[1]]()
