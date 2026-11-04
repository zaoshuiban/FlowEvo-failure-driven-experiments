"""Deterministic metadata-only task preparation; no model transport imported."""
import json,re,hashlib,sys,collections,os,csv
from pathlib import Path
from fractions import Fraction
from difflib import SequenceMatcher
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from code_math.private_math_scoring import normalized,extract_answer
from code_math.discovery_continuation import grade_continuation
from code_math.no_gold import PublicMathTask,solver_messages
from failure_evo.contracts import fingerprint,canonical
RAW=ROOT/'runs/hard140_algorithm_20261028_01/private'
OUT=ROOT/'datasets/math_long_stream200_20261102'
SUBJECTS=['algebra','counting_and_probability','geometry','intermediate_algebra','number_theory','prealgebra','precalculus']
VERSION='math-long-stream200-data-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub(r'\s+',' ',s).strip().lower()
def mask(s):return re.sub(r'\d+','N',norm(s))
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def save_lines(p,rows):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(canonical(r)+'\n' for r in rows))
def reference(solution):
 # Independently extract balanced last boxed expression, never fall back to last line.
 starts=list(re.finditer(r'\\boxed\s*\{',solution))
 if not starts:return None
 start=starts[-1].end();level=1;end=None
 for i in range(start,len(solution)):
  if solution[i]=='{':level+=1
  elif solution[i]=='}':level-=1
  if level==0:end=i;break
 if end is None:return None
 s=solution[start:end].strip().replace('\\dfrac','\\frac').replace('\\tfrac','\\frac')
 s=re.sub(r'\s+','',s)
 if re.fullmatch(r'-?\d{1,3}(?:,\d{3})+(?:\.\d+)?',s):s=s.replace(',','')
 m=re.fullmatch(r'(-?)\\frac\{(-?\d+)\}\{(-?\d+)\}',s)
 if m:s=('-' if m[1] else '')+m[2]+'/'+m[3]
 if not re.fullmatch(r'-?\d+(?:/[-+]?\d+|\.\d+)?',s):return None
 try:value=Fraction(s)
 except (ZeroDivisionError,ValueError):return None
 if normalized(extract_answer(solution))!=('rational',str(value)):return None
 return dict(raw_box=solution[start:end].strip(),canonical_answer=str(value))
def history():
 known={};inventory=[]
 def walk(v,path):
  if isinstance(v,dict):
   for k,x in v.items():
    if k in ('problem','prompt','question','problem_text','task_prompt') and isinstance(x,str) and 20<=len(x)<=24000:
     n=norm(x);known.setdefault(n,set()).add(str(path))
    elif isinstance(x,(dict,list)):walk(x,path)
  elif isinstance(v,list):
   for x in v:walk(x,path)
 roots=[ROOT/'runs',ROOT/'reports',ROOT.parent/'experiments']
 for base in roots:
  for p in sorted(base.rglob('*')):
   if not p.is_file() or p.suffix not in ('.json','.jsonl'):continue
   rel=str(p.relative_to(base));low=rel.lower();name=p.name.lower()
   if any(x in p.parts for x in ('frozen_source','private','.git','node_modules','__pycache__')):continue
   if any(x in name for x in ('private','sealed','gold','solution','label')):continue
   if not any(x in name for x in ('task','prompt','roles','bundle','evidence','public','cases','manifest','failures')):continue
   rec=dict(path=str(p),bytes=p.stat().st_size)
   if rec['bytes']>25_000_000:rec['status']='SIZE_LIMIT_NOT_READ';inventory.append(rec);continue
   try:
    if p.suffix=='.json':walk(json.loads(p.read_text()),p)
    else:
     for line in p.read_text().splitlines():
      if line.strip():walk(json.loads(line),p)
    rec.update(status='SCANNED',sha256=sha(p))
   except (ValueError,UnicodeError) as e:rec.update(status='READ_ERROR',error=type(e).__name__)
   inventory.append(rec)
 return known,inventory

def main():
 OUT.mkdir(parents=True,exist_ok=False)
 known,inventory=history();print('HISTORY',len(known),'files',len(inventory),flush=True)
 knownmasked={mask(k):k for k in known}
 # Length bins reduce exact SequenceMatcher calls without changing threshold.
 buckets=collections.defaultdict(list)
 for m in sorted(knownmasked):buckets[len(m)//100].append(m)
 def near(m,groups):
  lo=int(len(m)*.9/1.1);hi=int(len(m)*1.1/.9)+1
  for bucket in range(lo//100,hi//100+1):
   for other in groups.get(bucket,[]):
    if 2*min(len(m),len(other))/(len(m)+len(other))<.9:continue
    seq=SequenceMatcher(None,m,other,autojunk=False)
    if seq.quick_ratio()>=.9 and seq.ratio()>=.9:return other
  return None
 pools={};funnel=[];rawmeta={};reasons=collections.Counter()
 for subject in SUBJECTS:
  p=RAW/(subject+'.parquet');rows=pq.read_table(p).to_pylist();pools[subject]=[]
  rawmeta[subject]=dict(rows=len(rows),level5=sum(x['level']=='Level 5' for x in rows),sha256=sha(p),schema=str(pq.read_schema(p)))
  for index in sorted(range(len(rows)),key=lambda i:fingerprint([VERSION,subject,i])):
   x=rows[index];reason=None;ref=None;matched=None
   if x['level']!='Level 5':reason='NOT_LEVEL5'
   elif '[asy]' in x['problem'] or re.search(r'(?i)\b(diagram|figure shown|shown below|pictured|shaded region)\b',x['problem']):reason='VISUAL_REQUIRED_OR_UNCERTAIN'
   elif len(x['problem'].encode())>9000:reason='PUBLIC_INPUT_TOO_LONG'
   elif not (ref:=reference(x['solution'])):reason='NOT_STRICT_EXACT_RATIONAL_REFERENCE'
   elif norm(x['problem']) in known:reason='EXPOSED_EXACT';matched=norm(x['problem'])
   elif mask(x['problem']) in knownmasked:reason='EXPOSED_PARAMETER_TEMPLATE';matched=knownmasked[mask(x['problem'])]
   else:
    hit=near(mask(x['problem']),buckets)
    if hit is not None:reason='EXPOSED_NEAR_TEMPLATE';matched=knownmasked[hit]
   tid=f'math-stream200-train-{subject}-{index}'
   record=dict(task_id=tid,subject=subject,row=index,reason=reason or 'ELIGIBLE')
   if matched:record['exposure_references']=sorted(known[matched]);record['matched_problem_sha256']=fingerprint(matched)
   funnel.append(record);reasons[record['reason']]+=1
   if reason:continue
   pools[subject].append(dict(task_id=tid,problem=x['problem'],subject=subject,row=index,reference=ref,solution_sha256=fingerprint(x['solution'])))
  print('ELIGIBLE',subject,len(pools[subject]),flush=True)
 # Deterministic balanced round-robin, skips exhausted strata without lowering difficulty.
 selected=[];selectedmasks=collections.defaultdict(list);within=[];positions={s:0 for s in SUBJECTS}
 while len(selected)<200:
  advanced=False
  for s in SUBJECTS:
   while positions[s]<len(pools[s]):
    x=pools[s][positions[s]];positions[s]+=1;hit=near(mask(x['problem']),selectedmasks)
    if hit is not None:within.append(dict(task_id=x['task_id'],reason='WITHIN_STREAM_TEMPLATE_NEAR_DUPLICATE',matched_mask_sha256=fingerprint(hit)));continue
    selected.append(x);selectedmasks[len(mask(x['problem']))//100].append(mask(x['problem']));advanced=True;break
   if len(selected)==200:break
  if not advanced:break
 public=[dict(task_id=x['task_id'],problem=x['problem']) for x in selected]
 metadata=[];private=[];checks=[]
 for i,x in enumerate(selected):
  params=dict(sequence=i+1,batch=i//20+1,task_id=x['task_id'],subject=x['subject'],difficulty='Level 5',dataset='EleutherAI/hendrycks_math',split='train',dataset_row=x['row'],revision='21a5633873b6a120296cce3e2df9d5550074f4a3',
   original_problem_id=None,original_problem_url=None,record_locator=f"https://huggingface.co/datasets/EleutherAI/hendrycks_math/viewer/{x['subject']}/train?row={x['row']}",
   problem_sha256=fingerprint(x['problem']),normalized_problem_sha256=fingerprint(norm(x['problem'])),template_proxy_sha256=fingerprint(mask(x['problem'])),
   lineage_status='DISTINCT_DATASET_RECORD_AND_TEXT_TEMPLATE; ORIGINAL_CONTEST_LINEAGE_UNVERIFIED',evaluation_window='WARMUP_PREQUENTIAL' if i<40 else 'PRIMARY_PREQUENTIAL')
  metadata.append(params);gold=x['reference']['canonical_answer'];task=PublicMathTask.parse(public[i])
  private.append(dict(task_id=x['task_id'],problem_sha256=fingerprint(x['problem']),gold_answer=gold,reference_raw_box=x['reference']['raw_box'],solution_sha256=x['solution_sha256'],scoring='strict-rational-reference-v1'))
  wire=solver_messages(task,profile='concise-v1');wire_upper=len(canonical(wire).encode())+4096
  q=Fraction(gold);bad=str(q+1)
  tests=dict(reference_accepted=grade_continuation('The answer is '+gold,gold,'stop')['status']=='CONFIRMED_CORRECT',
   altered_answer_rejected=grade_continuation('The answer is '+bad,gold,'stop')['status']=='CONFIRMED_WRONG',
   truncated_not_failure=grade_continuation('25',gold,'length')['status']=='TRUNCATED',
   missing_answer_not_failure=grade_continuation('Unfinished calculation',gold,'stop')['status']=='EXECUTION_ERROR',
   unknown_expression_not_failure=grade_continuation('The answer is x+y',gold,'stop')['status']=='UNVERIFIED',
   public_fields_only=set(public[i])=={'task_id','problem'},first_call_input_fits=wire_upper<=32768)
  assert all(tests.values()),x['task_id'];checks.append(dict(task_id=x['task_id'],checks=tests,initial_input_upper=wire_upper))
 save_lines(OUT/'public/tasks.jsonl',public);save_lines(OUT/'host/task_metadata.jsonl',metadata)
 save_lines(OUT/'private/scoring.jsonl',private);os.chmod(OUT/'private',0o700);os.chmod(OUT/'private/scoring.jsonl',0o600)
 save(OUT/'audit/exposure_inventory.json',inventory);save(OUT/'audit/screening_funnel.json',funnel);save(OUT/'audit/within_stream_rejections.json',within);save(OUT/'audit/scorer_acceptance.json',checks)
 save(OUT/'host/batches.json',[dict(batch=i+1,task_ids=[r['task_id'] for r in public[i*20:(i+1)*20]]) for i in range((len(public)+19)//20)])
 counts=dict(collections.Counter(x['subject'] for x in selected))
 files={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()}
 protocol=dict(version=VERSION,date='2026-11-02',requested_tasks=200,prepared_tasks=len(public),status='DATA_PREPARED_EXECUTION_NOT_AUTHORIZED',model_calls=0,
  raw=rawmeta,selection='metadata only; Level5; strict rational answer; text-only; all recorded/reserved public candidates excluded; deterministic subject interleave; no target model outcomes',
  source_revision=json.loads((RAW/'dataset_revision.json').read_text()),source_url='https://huggingface.co/datasets/EleutherAI/hendrycks_math',
  counts=counts,eligible_counts={k:len(v) for k,v in pools.items()},funnel_first_reason=dict(reasons),within_rejections=len(within),
  known_public_texts=len(known),history_files=len(inventory),history_omissions=[r for r in inventory if r['status']!='SCANNED'],
  stream='200 ordered tasks,10 batches of20,one cold start per arm; first40 warmup scored but primary later160; no resets',
  scorer='grade_continuation, explicit final answer; rational exact mismatch only confirms wrong; symbolic nonmatch UNVERIFIED; truncation separate',
  limitations=['rational-answer subset not all hard mathematics','official Level5 does not guarantee target-model failures','not proven original contest lineage or pretraining novelty','approximate dedup cannot exclude semantic paraphrases','metadata/curation exposure is not solver exposure','filesystem split is not process-level isolation','full second-call wire must be checked at runtime'],
  files=files,preparation_script_sha256=sha(Path(__file__)),scorer_source_hashes={n:sha(ROOT/'FlowEvo/src'/n) for n in ['code_math/discovery_continuation.py','code_math/private_math_scoring.py','failure_evo/math_discovery_p1p2.py','code_math/no_gold.py']})
 save(OUT/'protocol.json',protocol);save(OUT/'freeze.json',dict(protocol_sha256=sha(OUT/'protocol.json'),public_tasks_sha256=sha(OUT/'public/tasks.jsonl')))
 with (OUT/'host/task_list.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(metadata[0]));w.writeheader();w.writerows(metadata)
 print('PREPARED',len(public),counts,'hash',sha(OUT/'protocol.json'),flush=True)
if __name__=='__main__':main()
