"""Paired development evaluation. Match outputs lock before private gold is loaded."""
import json,sys,time,collections
from pathlib import Path
from run_math_v3_development import ROOT,DATA,WORKER,IMAGE,save,sha
from failure_evo.semantic_contract import SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from code_math.no_gold import PublicMathTask
OLD=ROOT/'runs/math_v3_components_deepseek_repair_20261027_01'
TESTS=ROOT/'runs/math_v3_generated_tests_review_20261027_01'
def load(p):return json.loads(p.read_text())
def run(out):
 if not (out/'GENERATION_COMPLETE.json').exists():raise RuntimeError('generation incomplete')
 dest=out/'development'
 if dest.exists():raise RuntimeError('no rerun/overwrite')
 sourcecases=load(out/'cases.json');inputs=load(out/'inputs.json');plan=load(out/'protocol.json');assert fingerprint(sourcecases)==plan['cases_sha256']
 cases=[]
 for c in sourcecases:
  cases.append(dict(algorithm=c['algorithm'],role=c['role'],task=c['task'],supported=c['supported'],parameters=c['parameters'],old_observed=c['old_observed']))
 # Existing independent semantic reviews only. Do not copy oracle answers into execute projection.
 tr=load(TESTS/'scores.json')
 for name in ['F1','F2','F3','T3']:
  props=load(OLD/name/'test_proposals.json')
  for r in tr:
   if r['label']!='DS_'+name:continue
   problem=props[r['index']]['proposal']['problem'];cases.append(dict(algorithm=name,role='GeneratedDevelopment',task=dict(task_id='proposal-'+fingerprint(problem)[:16],problem=problem),supported=True if r['decision']=='positive' else False if r['decision']=='negative' else None,parameters=None,proposal_index=r['index'],old_observed=r['observation']))
 save(dest/'cases.json',cases);save(dest/'freeze.json',dict(cases_sha256=fingerprint(cases),script_sha256=sha(__file__),algorithm_hashes={k:v['solver_sha256'] for k,v in inputs.items()},selection='All 48 Design, all own sources, all previous same-algorithm generated controls. Labels from prior independent development review; no Gate access.',metrics='MATCH+correct / supported; MATCH+APPLIED / unsupported; UNKNOWN / decidable; ERROR separately; ambiguous excluded from rates'))
 (dest/'validator_source.py').write_bytes(Path(__file__).read_bytes())
 runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),dest/'worker.jsonl');outputs=[]
 for c in cases:
  for condition in ('OLD','F','T'):
   if condition=='OLD':o=c['old_observed']
   else:
    key=c['algorithm']+'_'+condition;p=out/key/'artifact.json'
    if p.exists():
     a=load(p);assert a['solver_sha256']==inputs[key]['solver_sha256'];o=runner.run(a,PublicMathTask.parse(c['task']))
    else:o=dict(status='NOT_GENERATED',match={'status':'NOT_GENERATED'})
   outputs.append(dict(algorithm=c['algorithm'],condition=condition,role=c['role'],task_id=c['task']['task_id'],problem_sha256=fingerprint(c['task']['problem']),supported=c['supported'],parameters=c['parameters'],proposal_index=c.get('proposal_index'),observation=o))
  if len(outputs)%150==0:print('locked',len(outputs),flush=True)
 save(dest/'outputs_locked.json',outputs);save(dest/'lock.json',dict(sha256=sha(dest/'outputs_locked.json'),at=time.time()))
 # Private evaluator, after every model request and Worker output is complete.
 from code_math.private_math_scoring import normalized
 private={r['task_id']:r for file in ['discovery.jsonl','design.jsonl'] for r in [json.loads(l) for l in (DATA/'private'/file).read_text().splitlines()]}
 proposal_private={(r['label'],r['index']):r for r in load(TESTS/'private/reviews.json')}
 for r in outputs:
  o=r['observation'];m=o['match'];gold=None;parameters=r['parameters']
  if r['role']=='GeneratedDevelopment':
   ref=proposal_private[('DS_'+r['algorithm'],r['proposal_index'])];gold=ref['reference_answer'];parameters=ref['parameters']
  else:gold=private[r['task_id']]['gold_answer']
  r['math']='NOT_APPLIED'
  if o['status']=='APPLIED':
   if gold is None:r['math']='UNVERIFIED'
   else:
    a,b=normalized(o['answer']),normalized(gold);r['math']='CORRECT' if a==b else 'WRONG' if a[0]==b[0]=='rational' else 'UNVERIFIED'
  got=m.get('parameters');eq=got==parameters
  if isinstance(got,dict) and isinstance(parameters,dict):
   if set(got)==set(parameters)=={'expression'}:eq=got['expression'].split()==parameters['expression'].split()
   elif 'digits' in parameters:
    eq=set(got.get('digits',[]))==set(parameters['digits']) and got.get('max_length',4)==parameters.get('max_length',4) and (0 not in parameters['digits'] or got.get('allow_leading_zero',False)==parameters.get('allow_leading_zero',False))
  r['parameter_valid']=eq if m['status']=='MATCH' and r['supported'] else None
  r['correct_accept']=r['supported'] is True and m['status']=='MATCH' and r['math']=='CORRECT'
  r['false_accept']=r['supported'] is False and m['status']=='MATCH' and o['status']=='APPLIED'
  r['ambiguous_accept']=r['supported'] is None and m['status']=='MATCH'
  r['interface_error']=o['status']=='ERROR'
 save(dest/'scores.json',outputs)
 summary={}
 for name in ['F1','F2','T2','F3','T3']:
  summary[name]={}
  for condition in ('OLD','F','T'):
   summary[name][condition]={}
   for role in ('Source','Design','GeneratedDevelopment'):
    rs=[r for r in outputs if (r['algorithm'],r['condition'],r['role'])==(name,condition,role)]
    pos=sum(r['supported'] is True for r in rs);neg=sum(r['supported'] is False for r in rs);dec=pos+neg
    ca=sum(r['correct_accept'] for r in rs);fa=sum(r['false_accept'] for r in rs);u=sum(r['supported'] is not None and r['observation']['match']['status']=='UNKNOWN' for r in rs)
    summary[name][condition][role]=dict(n=len(rs),supported=pos,unsupported=neg,ambiguous=len(rs)-dec,correct_accept=ca,correct_accept_rate=ca/pos if pos else None,false_accept=fa,false_accept_rate=fa/neg if neg else None,unknown=u,unknown_rate=u/dec if dec else None,interface_error=sum(r['interface_error'] for r in rs),interface_error_rate=sum(r['interface_error'] for r in rs)/len(rs) if rs else None,ambiguous_accept=sum(r['ambiguous_accept'] for r in rs),status_counts=dict(collections.Counter(r['observation']['match']['status'] for r in rs)),math_counts=dict(collections.Counter(r['math'] for r in rs)),parameter_mismatches=sum(r['parameter_valid'] is False for r in rs))
 save(dest/'summary.json',summary)
 candidates=[]
 for name in summary:
  for condition in ('F','T'):
   rs=[r for r in outputs if r['algorithm']==name and r['condition']==condition];supported=[r for r in rs if r['supported'] is True]
   passed=bool(supported) and all(r['correct_accept'] and r['parameter_valid'] is not False for r in supported) and not any(r['false_accept'] or r['interface_error'] or r['ambiguous_accept'] or r['observation']['status']=='NOT_GENERATED' for r in rs)
   # Unknown negative cases are safe fallback, not counted as correct explicit refusal.
   entry=dict(algorithm=name,condition=condition,development_passed=passed,status='FROZEN_FOR_FUTURE_GATE' if passed else 'SHADOW',gate_executed=False)
   if (out/(name+'_'+condition)/'artifact.json').exists():entry['artifact']=load(out/(name+'_'+condition)/'artifact.json')
   candidates.append(entry)
 save(out/'gate_readiness.json',candidates)
 save(out/'algorithm_integrity.json',{k:sha(out/k/'solver.py')==v['solver_sha256'] for k,v in inputs.items()})
 print('DONE; gate ready',sum(x['development_passed'] for x in candidates),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
