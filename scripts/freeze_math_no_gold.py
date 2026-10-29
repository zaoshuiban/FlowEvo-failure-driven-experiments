"""Zero-model data preparation. Legacy generator/oracles stay host-private.

Imports original functions solely in this offline command. Neither the solver,
compiler nor operator runtime imports this script or the archived legacy source.
"""
import argparse,collections,hashlib,json,random,re,shutil,socket,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint
from code_math.private_math_scoring import extract_answer,answer_equal

LEGACY=(160021,170031,170051,170071,170091)
FRESH=(270031,270051,270071,270091,270111)
ROLE_SEEDS={'Discovery':(260101,260103),'Design':(260201,),'Gate':(260301,), 'Legacy Test':LEGACY,'Fresh Test':FRESH}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readlines(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def normalized_problem(s):return ' '.join(s.replace('\\cdot','*').replace('\\times','*').split())
def lineage(row):
 m=row.get('mechanism_metadata',{});params=m.get('parameters')
 if params:return fingerprint(params)
 if m.get('near_miss_kind') and 'restricted' in m.get('family',''):
  return fingerprint(['digit-boundary',re.findall(r'\d+',row['problem']),m['near_miss_kind']])
 return fingerprint(normalized_problem(row['problem']))
def write(path,value,jsonl=False):
 path.parent.mkdir(parents=True,exist_ok=True)
 text=''.join(canonical(r)+'\n' for r in value) if jsonl else canonical(value)+'\n'
 if path.exists() and path.read_text()!=text:raise ValueError('frozen artifact differs: '+str(path))
 path.write_text(text)

def freeze(output,aflow):
 out=Path(output).resolve();aflow=Path(aflow).resolve()
 if (out/'manifest.json').exists():raise ValueError('already frozen; audit instead of regeneration')
 private=out/'private';private.mkdir(parents=True,exist_ok=True)
 # Explicitly block all network while restoring and generating the task pool.
 old_connect=socket.socket.connect
 socket.socket.connect=lambda *args,**kw:(_ for _ in ()).throw(RuntimeError('NO_NETWORK_DATA_PREPARATION'))
 sys.path.insert(0,str(aflow))
 try:
  import scripts.joint_two_operator_confirmation as legacy
  source_files=['scripts/joint_two_operator_confirmation.py','scripts/baseline_failure_mechanisms_v2.py','scripts/baseline_failure_mechanisms.py','scripts/parenthesization_v2_upgrade.py','scripts/restricted_prime_v2_confirmation.py','scripts/router_end_to_end_experiment.py','scripts/parameterized_tools.py','scripts/restricted_prime_tool.py','scripts/operator_library.py']
  source_hashes={}
  for name in source_files:
   source=aflow/name;target=private/'original_sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);source_hashes[name]=sha(source)
  source_math=aflow/'data/datasets/math_test.jsonl'
  shutil.copyfile(source_math,private/'original_math_test.jsonl')
  occupied=set();problems=set();parameters=set();roles={k:[] for k in ROLE_SEEDS};legacy_files={};rejections=[]
  for seed in LEGACY:
   directory=aflow/f'workspace/MATH/router_end_to_end/two_operator_joint_hidden_seed{seed}'
   source=directory/'mixed_hidden.jsonl';rows=readlines(source)
   if len(rows)!=48:raise ValueError('historical seed size differs')
   target=private/f'original_legacy_{seed}.jsonl';shutil.copyfile(source,target);legacy_files[str(seed)]=dict(path=str(source),sha256=sha(source))
   for i,row in enumerate(rows):
    occupied.add(legacy.stable_problem_id(row['problem']));problems.add(normalized_problem(row['problem']));parameters.add(lineage(row));roles['Legacy Test'].append((seed,i,row))
  def accept(rows,chosen,target_count,role,seed):
   for row in rows:
    if len(chosen)>=target_count:break
    p=normalized_problem(row['problem']);g=lineage(row)
    if p in problems or g in parameters:
     rejections.append(dict(role=role,seed=seed,problem_sha256=fingerprint(p),reason='CROSS_ROLE_OR_WITHIN_NEW_POOL_DUPLICATE'));continue
    chosen.append(row);problems.add(p);parameters.add(g);occupied.add(legacy.stable_problem_id(row['problem']))
  def batch(role,seed):
   groups=[]
   for family,count,offset,render in ((legacy.PARENTHESIZATION_MECHANISM,8,100003,legacy._decorate_parenthesization),(legacy.RESTRICTED_DIGIT_PRIME_MECHANISM,8,200003,legacy._decorate_prime)):
    chosen=[]
    for attempt in range(100):
     candidates=legacy._unique_rows(family,seed=seed+offset+attempt*7919,count=count,split='new_math_no_gold',occupied=set(occupied),difficulty='hard')
     accept([render(row,i) for i,row in enumerate(candidates)],chosen,count,role,seed)
     if len(chosen)==count:break
    if len(chosen)!=count:raise ValueError('finite generator pool exhausted')
    groups.extend(chosen)
   negatives=legacy._math_negatives(path=source_math,seed=seed+300007,count=24,occupied=occupied)
   chosen=[];accept(negatives,chosen,24,role,seed)
   if len(chosen)!=24:raise ValueError('not enough disjoint natural negatives')
   groups.extend(chosen)
   for make,offset in ((legacy._parenthesization_near_misses,400009),(legacy._prime_near_misses,500009)):
    chosen=[]
    for attempt in range(100):
     accept(make(seed=seed+offset+attempt*7919,count=4),chosen,4,role,seed)
     if len(chosen)==4:break
    if len(chosen)!=4:raise ValueError('boundary generator exhausted')
    groups.extend(chosen)
   random.Random(seed+600011).shuffle(groups)
   return [(seed,i,row) for i,row in enumerate(groups)]
  for role in ('Discovery','Design','Gate','Fresh Test'):
   for seed in ROLE_SEEDS[role]:roles[role].extend(batch(role,seed))
  counts={};role_ids={};role_lineages={};score_audit=[];schedules=[];private_counts={}
  for role,entries in roles.items():
   public=[];hidden=[]
   for seed,i,row in entries:
    prompt=row['problem'];tid='math-'+hashlib.sha256(prompt.encode()).hexdigest()[:24];metadata=row.get('mechanism_metadata',{})
    gold=str(metadata['oracle_answer']) if 'oracle_answer' in metadata else extract_answer(row['solution'])
    if not gold.strip():raise ValueError('empty reference answer')
    public.append(dict(task_id=tid,problem=prompt))
    hidden.append(dict(task_id=tid,problem_sha256=fingerprint(prompt),gold_answer=gold,solution=row['solution'],seed=seed,ordinal=i,
       parameter_lineage=lineage(row),family=metadata.get('family','unknown'),original_metadata=metadata,role=role))
    if not answer_equal('The answer is '+gold,gold) or answer_equal('P0_INVALID_ANSWER_SENTINEL',gold):raise ValueError('scorer transport roundtrip failed')
    score_audit.append(dict(task_id=tid,reference_roundtrip=True,invalid_rejected=True,independent_math_oracle_checked=False))
    for repeat in range(3 if role in ('Legacy Test','Fresh Test') else 1):schedules.append(dict(role=role,seed=seed,task_id=tid,repeat_id=repeat))
   slug=role.lower().replace(' ','_')
   write(out/'public'/f'{slug}.jsonl',public,True);write(private/f'{slug}.jsonl',hidden,True)
   counts[role]=len(public);role_ids[role]=set(p['task_id'] for p in public);role_lineages[role]=set(p['parameter_lineage'] for p in hidden)
   private_counts[role]=dict(collections.Counter(x['family'] for x in hidden))
  for i,role in enumerate(roles):
   for other in list(roles)[i+1:]:
    if role_ids[role]&role_ids[other] or role_lineages[role]&role_lineages[other]:raise ValueError('role isolation failed')
  write(out/'schedule.json',schedules)
  write(private/'family_counts.json',private_counts);write(out/'scorer_transport_acceptance.json',score_audit)
  write(out/'duplicate_exclusions.json',rejections)
  write(out/'generator_provenance.json',dict(original_generator_found=True,original_source_root=str(aflow),original_source_sha256=source_hashes,
   historical_task_files=legacy_files,legacy_exact_problem_restore=True,original_generator_runtime_snapshot_not_proven=True,
   original_occupied_workspace_snapshot_unavailable=True,new_generation='same original distributions and rendering, explicit deterministic cross-role dedup; not bitwise replay of past workspace-dependent generation',
   natural_pool_sha256=sha(source_math),private_original_code_never_model_visible=True))
  files={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
  write(out/'manifest.json',dict(version='math-no-gold-data-v1',counts=counts,seeds=ROLE_SEEDS,files=files,
    role_overlap=0,legacy_parameter_unique=len(role_lineages['Legacy Test']),legacy_prompt_unique=len(role_ids['Legacy Test']),
    formal_independent_prompts_per_arm=480,formal_runs_per_arm=1440,legacy_runs_per_arm=720,fresh_runs_per_arm=720,
    public_schema=['task_id','problem'],private_answers_host_only=True,api_requests=0,
    scoring_acceptance='transport/normalization only; not independent proof that every historical reference solution is mathematically correct',
    study_distribution='restored historically targeted parameterized mix, not representative natural mathematics'))
 finally:socket.socket.connect=old_connect
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',default=str(ROOT/'reports/math_no_gold_p0_20261027/data'));p.add_argument('--aflow',default='/Users/majiatong/lab/AFlow');a=p.parse_args()
 print(freeze(a.output,a.aflow))
