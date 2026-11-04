"""Metadata/source-only preparation. Does NOT invoke models, candidate algorithms or Gate."""
import json,re,collections,csv,os
from pathlib import Path
from fractions import Fraction
from difflib import SequenceMatcher
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_stream import read,save,sha
from code_math.discovery_continuation import grade_continuation
from code_math.no_gold import PublicMathTask,solver_messages
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'datasets/math_cumulative50_20261103'
VERSION='math-cumulative50-data-v1'
QUOTAS={'finite_combinatorics_counting':17,'number_theory_discrete_probability':17,'algebra_discrete_optimization':16}
def lines(p,rows):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(canonical(x)+'\n' for x in rows))
def norm(t):return re.sub(r'\s+',' ',t).strip().lower()
def mask(t):return re.sub(r'\d+','N',norm(t))
def main():
 if (D/'freeze.json').exists():raise PermissionError('data already frozen; explicit new version required')
 candidates=read(D/'private/candidate_catalog.json')
 # Earlier inventory is immutable input, excludes current preparation. Read question fields ONLY.
 inventory=read(D/'audit/prior_inventory.json');known={}
 def visit(x,path):
  if isinstance(x,dict):
   for k,v in x.items():
    if k in ('problem','prompt','question','problem_text','task_prompt') and isinstance(v,str) and 20<=len(v)<=24000:known.setdefault(norm(v),set()).add(path)
    elif isinstance(v,(dict,list)):visit(v,path)
  elif isinstance(x,list):
   for v in x:visit(v,path)
 for r in inventory:
  p=Path(r['path'])
  if r['status']!='SCANNED' or not p.exists():continue
  if sha(p)!=r['sha256']:raise PermissionError('historical input inventory changed '+str(p))
  try:
   for x in ([read(p)] if p.suffix=='.json' else [json.loads(l) for l in p.read_text().splitlines()]):visit(x,str(p))
  except (ValueError,UnicodeError):raise
 for p in [ROOT/'datasets/math_long_stream200_20261102/public/tasks.jsonl',ROOT/'datasets/math_olympiad_three_domain200_20261102/public/tasks.jsonl']:
  for line in p.read_text().splitlines():visit(json.loads(line),str(p))
 previous=read(ROOT/'runs/math_stream200_provenance_gate_20261102_01/provenance.json')
 exposed_originals={r['source_original_id'] for r in previous.values()}
 from audit_math_stream200_sources import grams
 # Dataset text is a secondary exposure check, NOT original identity evidence.
 omni=[json.loads(l) for l in (ROOT/'datasets/math_olympiad_three_domain200_20261102/private/Omni-Math.jsonl').read_text().splitlines()]
 om=[(i,x,grams(x['problem'])) for i,x in enumerate(omni) if x['source'].startswith('HMMT')]
 eligible=[];funnel=[]
 for r in candidates:
  oid='HMMT/'+r['key'].replace('-','/')+'/P'+str(r['item']);r['original_id']=oid
  g=grams(r['problem']);near=sorted([(len(g&gg)/max(1,len(g)),i,x) for i,x,gg in om],key=lambda t:-t[0])[:1]
  exposure=[]
  if oid in exposed_originals:exposure.append('PRIOR_VERIFIED_ORIGINAL')
  if norm(r['problem']) in known:exposure.append('PRIOR_EXACT_TEXT')
  if near and near[0][0]>=.6 and norm(near[0][2]['problem']) in known:exposure.append('PRIOR_HIGH_SIMILARITY_CONSERVATIVE_EXCLUSION')
  r['dataset_match_candidate']=dict(row=near[0][1],coverage=near[0][0],identity='TEXT_CANDIDATE_NOT_PROVENANCE')
  if near[0][0]>.85:r['difficulty_annotation']=dict(dataset='Omni-MATH',value=near[0][2]['difficulty'],status='SECONDARY_MATCH_NOT_OFFICIAL_RATING')
  r['exposure_status']='EXCLUDED' if exposure else 'NO_MATCH_IN_FROZEN_PROJECT_INVENTORY'
  funnel.append(dict(task_id=r['task_id'],category=r['category'],reason=exposure or ['ELIGIBLE'],original_id=oid))
  if not exposure:eligible.append(r)
 selected=[]
 for cat,count in QUOTAS.items():
  pool=sorted([r for r in eligible if r['category']==cat],key=lambda r:(-r['rank'],fingerprint([VERSION,r['task_id']])))
  if len(pool)<count:raise ValueError('insufficient '+cat+':'+str(len(pool)))
  chosen=pool[:count];chosen.sort(key=lambda r:fingerprint([VERSION,'order',r['task_id']]))
  selected.append(chosen)
 ordered=[pool[i] for i in range(17) for pool in selected if i<len(pool)]
 public=[];scores=[];meta=[];lineage={};checks=[]
 def source(key,kind):
  r=read(D/'private/sources'/('hmmt-'+key+'-'+kind+'.receipt.json'));p=D/'private/sources'/('hmmt-'+key+'-'+kind+'.pdf')
  if sha(p)!=r['sha256']:raise PermissionError('source drift')
  return dict(url=r['url'],pdf_sha256=r['sha256'])
 for seq,r in enumerate(ordered,1):
  tid=r['task_id'];public.append(dict(task_id=tid,problem=r['problem']));ref=source(r['key'],'solutions')
  scores.append(dict(task_id=tid,problem_sha256=fingerprint(r['problem']),gold_answer=r['answer'],oracle_sha256=fingerprint([ref,r['item'],r['answer']]),answer_source=ref,reference_status='ORGANIZER_REFERENCE_TRANSCRIBED_NOT_NEW_SOLVE'))
  record=dict(task_id=tid,sequence=seq,source_original_id=r['original_id'],lineage_id=r['original_id'],parameter_variant_id='ORIGINAL_PARAMETERS',dataset_role='PREQUENTIAL_STREAM',mechanism_family='UNKNOWN_UNTIL_LEARNED',research_stratum=r['category'],
   source=source(r['key'],'problems'),item=r['item'],source_identity='OFFICIAL_EDITION_ROUND_ITEM',problem_sha256=fingerprint(r['problem']),transcription=r['transcription'],exposure_status=r['exposure_status'],difficulty=dict(contest='HMMT',round=r['key'],item_order=r['rank'],not_calibrated=True),template_proxy_sha256=fingerprint(mask(r['problem'])))
  meta.append(record);lineage[tid]=record
 # Gate: earlier source-only preparation, no model learning; role change explicitly recorded.
 bank=ROOT/'runs/math_stream200_provenance_gate_20261102_01/bank';records=read(bank/'manifest.json');q={r['task_id']:r for r in read(bank/'Development.public.json')+read(bank/'private/Gate.questions.json')};bscore=read(bank/'private/scores.json');gate=[]
 for r in records:
  tid=r['task_id']
  if tid=='hmmt-2025-feb-comb-8':q[tid]['problem']=r'Albert writes 2025 numbers $a_1,\ldots,a_{2025}$ in a circle. Initially they are sampled independently and uniformly from [0,1]. Each second all entries are simultaneously replaced by $a_i\leftarrow\max(a_{i-1},a_i,a_{i+1})$, with $a_0=a_{2025}$ and $a_{2026}=a_1$. Compute the expected number of distinct values after 100 seconds.'
  gate.append(dict(task_id=tid,problem=q[tid]['problem'],original_id=r['source_original_id'],lineage_id=r['lineage_id'],answer=bscore[tid]['answer'],oracle_sha256=fingerprint(bscore[tid]),source=r['source'],answer_source=r['answer_source'],previous_role=r['dataset_role'],role='SEALED_GATE_CANDIDATE',preparation_exposure='SOURCE_PREPARATION_ONLY_NO_RECORDED_MODEL_USE',semantic_label='PENDING_EXACT_ARTIFACT_REVIEW'))
 for n,problem,answer in [(3,r'Given positive real numbers x,y,z such that $x^{\log_2(yz)}=2^8\cdot3^4$, $y^{\log_2(zx)}=2^9\cdot3^6$, and $z^{\log_2(xy)}=2^5\cdot3^{10}$, compute the smallest possible xyz.','1/576'),(6,r'Let r be the remainder when $2017^{2025!}-1$ is divided by $2025!$. Compute $r/(2025!)$. (2017 is prime.)','1311/2017')]:
  ref=source('2025-feb-algnt','solutions');oid='HMMT/2025/feb/algnt/P'+str(n)
  gate.append(dict(task_id='hmmt-2025-feb-algnt-'+str(n),problem=problem,original_id=oid,lineage_id=oid,answer=answer,oracle_sha256=fingerprint([ref,n,answer]),source=source('2025-feb-algnt','problems'),answer_source=ref,previous_role='NONE',role='SEALED_GATE_CANDIDATE',preparation_exposure='NEW_SOURCE_PREPARATION',semantic_label='PENDING_EXACT_ARTIFACT_REVIEW'))
 assert len(gate)==24 and not set(lineage)&{x['task_id'] for x in gate}
 assert not {x['source_original_id'] for x in meta}&{x['original_id'] for x in gate}
 # Expose NO answers in public task or provenance views.
 for r in [dict(task_id=x['task_id'],problem=x['problem'],answer=x['gold_answer']) for x in [dict(s,problem=t['problem']) for s,t in zip(scores,public)]]+gate:
  gold=r['answer'];t=PublicMathTask(r['task_id'],r['problem'])
  c=dict(reference=grade_continuation('The answer is '+gold,gold,'stop')['status']=='CONFIRMED_CORRECT',wrong=grade_continuation('The answer is '+str(Fraction(gold)+1),gold,'stop')['status']=='CONFIRMED_WRONG',truncated=grade_continuation('25',gold,'length')['status']=='TRUNCATED',unverified=grade_continuation('The answer is x+y',gold,'stop')['status']=='UNVERIFIED',input_preflight=len(canonical(solver_messages(t,profile='concise-v1')).encode())+4096<=32768)
  assert all(c.values()),r['task_id'];checks.append(dict(task_id=r['task_id'],checks=c))
 lines(D/'public/tasks.jsonl',public);lines(D/'host/metadata.jsonl',meta);save(D/'host/lineage.json',lineage);lines(D/'private/scoring.jsonl',scores)
 save(D/'private/gate_pool.json',dict(version='official-gate-pool-v1',origin='ORGANIZER_ARCHIVE',selection='Fixed 2025 edition pool before candidate generation; no online2025; all24 reviewed before deterministic first2positive+first2negative selection',cases=gate))
 save(D/'host/gate_manifest.json',[{k:v for k,v in r.items() if k not in ('answer','problem')} for r in gate])
 save(D/'audit/scorer_acceptance.json',checks);save(D/'audit/admission_funnel.json',funnel)
 with (D/'host/task_list.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['sequence','task_id','source_original_id','research_stratum']);w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in meta)
 save(D/'data_protocol.json',dict(version=VERSION,online_tasks=50,gate_candidates=24,quotas=QUOTAS,real_model_calls=0,selection='Known source and scalar official reference; exclude project exposure; rank item number within stratum then frozen hash interleave. Item number is a difficulty proxy, NOT a calibrated hardest-task rating.',gate_role_change='12 old source-preparation Development records become sealed candidates before any model use; 10 old Gate records retained; 2 newly transcribed.',learning_group_labels='Host only; no algorithm or mechanism hint sent',scoring='strict complete rational answer; official reference independent of generated candidate; not newly solved by independent program',limitations=['One contest family; not all mathematical distributions','No claim of pretraining novelty','Independent contest item does not prove no unrecorded adaptation','Pool cannot guarantee coverage of unknown future candidates','All74 scorer checks are transmission/parser checks, not74 independent algorithm solves']))
 save(D/'freeze.json',dict(version=VERSION,files={str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file() and p.name!='freeze.json'},ordered_tasks_sha256=fingerprint(public)))
 for p in (D/'private').rglob('*'):
  if p.is_file():p.chmod(0o600)
 print('FROZEN',len(public),len(gate),collections.Counter(r['research_stratum'] for r in meta))
if __name__=='__main__':main()
