"""Development only: freeze public cases and independent parameters; lock outputs before scoring.
No model API. Parameter mappings are evaluation adapters, never runtime operators.
"""
import json,sys,time,collections
from pathlib import Path
from run_math_v3_development import ROOT,DATA,WORKER,IMAGE,save,sha
from failure_evo.semantic_contract import SplitRunner,component_check
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from code_math.no_gold import PublicMathTask

def load(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def parameters(schema,metadata,group):
 p=metadata.get('original_metadata',{}).get('parameters',{})
 if not p:return None
 fields=set(schema['properties'])
 if group==1 and 'digits' in p:
  if fields=={'digit_set','max_length','forbid_leading_zero'}:return dict(digit_set=p['digits'],max_length=p['max_length'],forbid_leading_zero=True)
  if fields=={'digits','max_length','allow_leading_zero'}:return dict(digits=p['digits'],max_length=p['max_length'],allow_leading_zero=False)
 if group!=1 and 'numbers' in p:
  expression=' '.join(str(v) for pair in zip(p['numbers'],p['operators']+['']) for v in pair if v!='')
  if fields=={'expression'}:return dict(expression=expression)
  if fields=={'numbers','operators'}:return dict(numbers=p['numbers'],operators=p['operators'])
  if fields=={'operands','operators'}:return dict(operands=p['numbers'],operators=p['operators'])
 return None

def run(runpath,out):
 if out.exists():raise RuntimeError('new audit only')
 evidence=load(runpath/'evidence.json');design=lines(DATA/'public/design.jsonl')
 # Host-only parameter projection: gold is not retained in these execution records.
 private={r['task_id']:r for r in lines(DATA/'private/discovery.jsonl')+lines(DATA/'private/design.jsonl')}
 targets={1:'restricted_digit_prime_enumeration',2:'parenthesization_distinct_value_dedup',3:'parenthesization_distinct_value_dedup'}
 jobs=[]
 for d in sorted(runpath.iterdir()):
  if not d.is_dir() or not (d/'solver_response.json').exists():continue
  response=load(d/'solver_response.json');code=response['code']
  if not component_check(code,'solve')['passed']:continue
  schema=json.loads(response['applicability']);g=int(d.name[1:]);art=load(d/'artifact.json') if (d/'artifact.json').exists() else None
  imported=load(d/'mechanism_import.json')['mechanism'];sources=[r['task'] for r in evidence if r['evidence_id'] in imported['source_evidence_ids']]
  for role,tasks in [('Source',sources),('Design',design)]:
   for t in tasks:
    meta=private[t['task_id']];supported=meta['family']==targets[g]
    jobs.append(dict(name=d.name,role=role,task=t,supported=supported,parameters=parameters(schema,meta,g) if supported else None,solver_path=str(d/'solver.py'),solver_sha256=sha(d/'solver.py'),artifact=art))
 freeze=dict(jobs=jobs,script_sha256=sha(__file__),input_hashes={str(p):sha(p) for p in [DATA/'public/design.jsonl',DATA/'private/design.jsonl',DATA/'private/discovery.jsonl']},semantic_review='Development host review: the 8 prime-count/no-repeat questions and 8 distinct-result questions are targets; alternate requested quantities, repeated digits, and unrelated tasks are negatives. Parameter adapters only rename frozen generator parameters, never use the candidate matcher. Full contract restrictions reported separately.',no_gate=True)
 save(out/'freeze.json',freeze);del private
 backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER);runner=SplitRunner(backend,out/'worker.jsonl');results=[]
 for j in jobs:
  assert sha(j['solver_path'])==j['solver_sha256']
  r={k:j[k] for k in ('name','role','supported','parameters','solver_sha256')};r['task_id']=j['task']['task_id']
  if j['artifact']:r['observed']=runner.run(j['artifact'],PublicMathTask.parse(j['task']))
  else:r['observed']=dict(status='NOT_GENERATED',match=dict(status='NOT_GENERATED'))
  if j['parameters'] is not None:
   start=time.monotonic()
   with backend(Path(j['solver_path'])) as w:r['independent_solve']=w.call(dict(mode='function',function='solve',args=[j['parameters']],timeout=2))
   r['independent_seconds']=time.monotonic()-start
  results.append(r)
 save(out/'outputs_locked.json',results);save(out/'lock.json',dict(sha256=sha(out/'outputs_locked.json'),at=time.time()))
 # No generation or revision follows these scores.
 from code_math.private_math_scoring import normalized
 private={r['task_id']:r for r in lines(DATA/'private/discovery.jsonl')+lines(DATA/'private/design.jsonl')}
 def grade(v,g):
  a,b=normalized(str(v)),normalized(g)
  return 'CORRECT' if a==b else 'WRONG' if a[0]==b[0]=='rational' else 'UNVERIFIED'
 for r in results:
  o=r['observed'];m=o['match'];g=private[r['task_id']]['gold_answer']
  r['combined']=grade(o['answer'],g) if o['status']=='APPLIED' else o['status']
  r['computation']='NOT_EVALUATED'
  if 'independent_solve' in r:
   c=r['independent_solve'];r['computation']=grade(c['value'],g) if c.get('status')=='OK' else 'ERROR'
  got=m.get('parameters');expected=r['parameters'];equivalent=got==expected
  if isinstance(got,dict) and isinstance(expected,dict) and r['name'].endswith('1'):
   key='digit_set' if 'digit_set' in expected else 'digits';flag='forbid_leading_zero' if key=='digit_set' else 'allow_leading_zero'
   equivalent=set(got)==set(expected) and set(got.get(key,[]))==set(expected[key]) and got.get('max_length')==expected['max_length'] and (0 not in expected[key] or got.get(flag)==expected[flag])
  r['parameter_equivalence']='Exact fields, except unordered digit set and irrelevant leading-zero flag when zero absent; frozen before DS audit'
  r['applicability']=('CORRECT_MATCH' if equivalent else 'PARAMETER_MISMATCH') if r['supported'] and m['status']=='MATCH' else ('FALSE_ACCEPT' if m['status']=='MATCH' else 'CORRECT_REFUSAL' if m['status']=='DECLINE' else m['status']) if not r['supported'] else m['status']
 save(out/'scores.json',results)
 summary={}
 for name in sorted({r['name'] for r in results}):
  summary[name]={role:{metric:dict(collections.Counter(r[metric] for r in results if r['name']==name and r['role']==role)) for metric in ('computation','applicability','combined')} for role in ('Source','Design')}
 save(out/'summary.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
