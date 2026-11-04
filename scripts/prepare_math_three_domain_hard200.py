"""Metadata-only Olympiad task selection. No model calls; preserve prior dataset."""
import sys,json,re,collections,shutil,os,csv,hashlib
from pathlib import Path
from fractions import Fraction
from difflib import SequenceMatcher
import prepare_math_long_stream200 as h
from code_math.no_gold import PublicMathTask,NoGoldMathController,NoGoldPolicy,solver_messages
from code_math.private_math_scoring import PrivateMathScorer
ROOT=h.ROOT
OUT=ROOT/'datasets/math_olympiad_three_domain200_20261102'
RUN=ROOT/'runs/math_olympiad_three_domain200_acceptance_20261102'
VERSION='omnimath-three-domain-hard200-v1'
SUBJECTS=['algebra','number_theory','combinatorics_probability']
QUOTAS=dict(algebra=67,number_theory=66,combinatorics_probability=67)
def category(x):
 d=(x.get('domain') or [''])[0]
 if d.startswith('Mathematics -> Algebra ->'):return 'algebra'
 if d.startswith('Mathematics -> Number Theory ->'):return 'number_theory'
 if d.startswith('Mathematics -> Discrete Mathematics ->') or ' -> Probability ->' in d:return 'combinatorics_probability'
 return None

def main():
 OUT.mkdir(parents=True,exist_ok=False);RUN.mkdir(parents=True,exist_ok=False)
 private=OUT/'private';private.mkdir(mode=0o700)
 raw=private/'Omni-Math.jsonl';shutil.copyfile('/tmp/flowevo-omnimath-source/Omni-Math.jsonl',raw);os.chmod(raw,0o600)
 provenance=json.loads(Path('/tmp/flowevo-omnimath-source/provenance.json').read_text());assert h.sha(raw)==provenance['sha256']
 rows=[json.loads(x) for x in raw.read_text().splitlines()]
 known,inventory=h.history()
 # Also exclude every prior locally frozen public math task list, including previous 200.
 for p in sorted((ROOT/'datasets').glob('*/public/tasks.jsonl')):
  if OUT in p.parents:continue
  for line in p.read_text().splitlines():
   x=json.loads(line)
   if isinstance(x.get('problem'),str):known.setdefault(h.norm(x['problem']),set()).add(str(p))
  inventory.append(dict(path=str(p),status='SCANNED_PUBLIC_DATASET',sha256=h.sha(p)))
 masked={h.mask(k):k for k in known};buckets=collections.defaultdict(list)
 for m in masked:buckets[len(m)//100].append(m)
 def near(m,groups):
  lo=int(len(m)*.9/1.1);hi=int(len(m)*1.1/.9)+1
  for b in range(lo//100,hi//100+1):
   for other in groups.get(b,[]):
    if 2*min(len(m),len(other))/(len(m)+len(other))<.9:continue
    s=SequenceMatcher(None,m,other,autojunk=False)
    if s.quick_ratio()>=.9 and s.ratio()>=.9:return other
  return None
 funnel=[];pools={s:[] for s in SUBJECTS}
 for i,x in enumerate(rows):
  s=category(x);reason=None;ref=None;hit=None
  if s is None:reason='OUTSIDE_THREE_PRIMARY_DOMAINS'
  elif not isinstance(x.get('difficulty'),(int,float)) or x['difficulty']<5:reason='BELOW_PREDECLARED_DIFFICULTY_FLOOR_5'
  elif re.search(r'(?i)\[asy\]|<img|!\[|\b(diagram|shown below|pictured|shaded region)\b',x['problem']):reason='VISUAL_OR_UNCERTAIN'
  elif re.search(r'(?i)\b(prove|show that|demonstrate that)\b',x['problem']):reason='PROOF_REQUIRED_NOT_SUPPORTED'
  elif len(x['problem'].encode())>9000:reason='INPUT_LIMIT'
  elif not (ref:=h.reference('\\boxed{'+x['answer']+'}')):reason='NOT_STRICT_RATIONAL_REFERENCE'
  elif h.norm(x['problem']) in known:reason='EXPOSED_EXACT';hit=h.norm(x['problem'])
  elif h.mask(x['problem']) in masked:reason='EXPOSED_TEMPLATE';hit=masked[h.mask(x['problem'])]
  else:
   n=near(h.mask(x['problem']),buckets)
   if n is not None:reason='EXPOSED_NEAR_TEMPLATE';hit=masked[n]
  record=dict(row=i,subject=s,difficulty=x.get('difficulty'),reason=reason or 'ELIGIBLE')
  if hit:record['exposure_files']=sorted(known[hit]);record['matched_problem_sha256']=h.fingerprint(hit)
  funnel.append(record)
  if not reason:pools[s].append(dict(row=i,**x,subject=s,reference=ref))
 print('ELIGIBLE', {s:len(v) for s,v in pools.items()},flush=True)
 # Highest source difficulty first within each category, SHA tie break. No outcome selection.
 for s in SUBJECTS:pools[s].sort(key=lambda x:(-x['difficulty'],h.fingerprint([VERSION,provenance['revision'],x['row']])))
 selected_by={s:[] for s in SUBJECTS};seen=collections.defaultdict(list);dedup=[]
 for s in SUBJECTS:
  for x in pools[s]:
   m=h.mask(x['problem']);hit=near(m,seen)
   if hit:dedup.append(dict(row=x['row'],reason='WITHIN_STREAM_NEAR_TEMPLATE'));continue
   selected_by[s].append(x);seen[len(m)//100].append(m)
   if len(selected_by[s])==QUOTAS[s]:break
 selected=[]
 # Once selection is complete, pseudo-randomize within category, then interleave.
 for s in SUBJECTS:selected_by[s].sort(key=lambda x:h.fingerprint([VERSION,'stream-order',x['row']]))
 for j in range(max(map(len,selected_by.values()))):
  for s in SUBJECTS:
   if j<len(selected_by[s]):selected.append(selected_by[s][j])
 pub=[];meta=[];scores=[];accept=[]
 for i,x in enumerate(selected):
  tid='omni-hard200-row-'+str(x['row']);problem=x['problem'];gold=x['reference']['canonical_answer']
  pub.append(dict(task_id=tid,problem=problem))
  meta.append(dict(sequence=i+1,batch=i//20+1,task_id=tid,subject=x['subject'],difficulty=x['difficulty'],source=x['source'],domain=x['domain'],dataset='KbsdJames/Omni-MATH',revision=provenance['revision'],row=x['row'],problem_sha256=h.fingerprint(problem),template_proxy_sha256=h.fingerprint(h.mask(problem)),source_record_url=provenance['url'],lineage_status='SOURCE_FAMILY_AND_DATASET_ROW_KNOWN; ORIGINAL_CONTEST_ITEM_UNVERIFIED'))
  scores.append(dict(task_id=tid,problem_sha256=h.fingerprint(problem),gold_answer=gold,raw_reference=x['answer'],solution_sha256=h.fingerprint(x['solution'])))
  tests=dict(reference_accept=h.grade_continuation('The answer is '+gold,gold,'stop')['status']=='CONFIRMED_CORRECT',wrong_reject=h.grade_continuation('The answer is '+str(Fraction(gold)+1),gold,'stop')['status']=='CONFIRMED_WRONG',truncation_separate=h.grade_continuation('25',gold,'length')['status']=='TRUNCATED',symbolic_unknown=h.grade_continuation('The answer is x+y',gold,'stop')['status']=='UNVERIFIED',public_allowlist=set(pub[-1])=={'task_id','problem'},initial_wire_fits=len(h.canonical(solver_messages(PublicMathTask.parse(pub[-1]),profile='concise-v1')).encode())+4096<=32768)
  assert all(tests.values());accept.append(dict(task_id=tid,checks=tests))
 h.save_lines(OUT/'public/tasks.jsonl',pub);h.save_lines(OUT/'host/task_metadata.jsonl',meta);h.save_lines(private/'scoring.jsonl',scores);os.chmod(private/'scoring.jsonl',0o600)
 h.save(OUT/'host/batches.json',[dict(batch=i//20+1,task_ids=[x['task_id'] for x in pub[i:i+20]]) for i in range(0,len(pub),20)])
 h.save(OUT/'audit/funnel.json',funnel);h.save(OUT/'audit/exposure_inventory.json',inventory);h.save(OUT/'audit/within_duplicates.json',dedup);h.save(OUT/'audit/scorer_checks.json',accept)
 with (OUT/'host/task_list.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(meta[0]));w.writeheader();w.writerows(meta)
 counts={s:len(selected_by[s]) for s in SUBJECTS}
 protocol=dict(version=VERSION,source=provenance,requested_tasks=200,prepared_tasks=len(pub),counts=counts,selection='first official domain determines category; rank source difficulty descending within category; stable SHA ties; fixed quotas; exclude exposure/templates; then SHA shuffle and category interleave',difficulty_floor=5,quotas=QUOTAS,difficulty_distribution=dict(collections.Counter(str(x['difficulty']) for x in selected)),per_category_difficulty={s:dict(collections.Counter(str(x['difficulty']) for x in selected_by[s])) for s in SUBJECTS},source_distribution=dict(collections.Counter(x['source'] for x in selected)),funnel=dict(collections.Counter(x['reason'] for x in funnel)),eligible_counts={s:len(v) for s,v in pools.items()},history_texts=len(known),history_files=len(inventory),history_omissions=[x for x in inventory if x['status'] not in ['SCANNED','SCANNED_PUBLIC_DATASET']],model_calls=0,status='DATA_PREPARED_NOT_MODEL_EXPERIMENT',previous_dataset='math_long_stream200_20261102 preserved',scoring='strict scalar rational answer; binary scoring only after lock; no official solutions to agents; not official Omni-MATH leaderboard protocol',limitations=['different datasets difficulty scales are not calibrated','top metadata difficulty within exact-answer subset, not all hardest proof tasks','subject is first official domain, multi-domain annotations retained','official reference not independently solved','original contest item lineage unverified','no pretraining novelty claim','first wire only; later request preflight required','private filesystem split does not enforce runtime process isolation'],preparation_script_sha256=h.sha(Path(__file__)),helper_sha256=h.sha(Path(h.__file__)),scorer_sha256=h.sha(ROOT/'FlowEvo/src/code_math/discovery_continuation.py'))
 protocol['files']={str(p.relative_to(OUT)):h.sha(p) for p in OUT.rglob('*') if p.is_file()}
 h.save(OUT/'protocol.json',protocol);h.save(OUT/'freeze.json',dict(protocol_sha256=h.sha(OUT/'protocol.json'),tasks_sha256=h.sha(OUT/'public/tasks.jsonl')))
 class Mock:
  task=None;step=0;count=0
  def generate_no_gold(self,**kw):
   assert kw['messages']==solver_messages(self.task,None if self.step==0 else 'The answer is 0',profile='concise-v1')
   assert set(kw)=={'messages','policy','request_id'}
   self.step+=1;self.count+=1
   return dict(text='The answer is 0',usage=dict(prompt_tokens=0,completion_tokens=0),reasoning_tokens=0,origin='MOCK',finish_reason='stop')
 mock=Mock();controller=NoGoldMathController(mock,RUN/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1'));scorer=PrivateMathScorer(scores,RUN/'controller.jsonl',RUN/'private_mock_scores.jsonl')
 for i,x in enumerate(pub):
  mock.task=PublicMathTask.parse(x);mock.step=0
  lock=controller.solve(mock.task,episode_id='engineering:omni200:'+str(i),sequence=i+1)
  assert mock.step==2 and lock['gold_exposed'] is False
  scorer.score(mock.task,lock)
 assert all(h.sha(OUT/f)==v for f,v in protocol['files'].items())
 h.save(RUN/'summary.json',dict(tasks=len(pub),mock_calls=mock.count,real_model_calls=0,scorer_checks_passed=sum(len(x['checks']) for x in accept),frozen_hashes_verified=True,exact_request_projection=True,private_scoring_after_lock=True,research_accuracy='NOT_MEASURED'))
 print(json.dumps({k:protocol[k] for k in ['prepared_tasks','counts','difficulty_distribution','per_category_difficulty','funnel','history_texts']},indent=2),flush=True)
if __name__=='__main__':main()
