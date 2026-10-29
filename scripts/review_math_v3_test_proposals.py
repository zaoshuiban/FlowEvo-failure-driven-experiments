"""Offline host semantic review of every proposal, using pre-existing reference code.
No model calls; no candidate code is imported as an oracle. No new math algorithm.
"""
import ast,json,sys,re,importlib.util,collections,time
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from run_math_v3_development import ROOT,DATA,WORKER,IMAGE,save,sha
from failure_evo.semantic_contract import SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from code_math.no_gold import PublicMathTask
from code_math.private_math_scoring import normalized
REF=DATA/'private/original_sources/scripts'
# Reviewed by host from full question and frozen contract, not model kind/claimed_behavior.
REVIEWS={
 'GPT_F1':['positive','positive','negative','negative','ambiguous','negative','ambiguous','ambiguous'],
 'DS_F1':['positive','negative','positive','positive','positive','positive','positive','positive'],
 'DS_F2':['positive','positive','negative','negative','positive','positive','positive','negative','ambiguous'],
 'DS_F3':['positive','positive','negative','negative','negative','positive','positive','positive','ambiguous'],
 'DS_T3':['positive','positive','negative','ambiguous','negative','ambiguous','positive','positive','ambiguous']}
def run(out):
 if out.exists():raise RuntimeError('new review only')
 # Load trusted pre-existing exact reference routines in this private host process only.
 path=REF/'restricted_prime_tool.py';spec=importlib.util.spec_from_file_location('private_prime_reference',path);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
 expr=REF/'baseline_failure_mechanisms_v2.py';tree=ast.parse(expr.read_text());func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_parenthesized_values');ns=dict(Fraction=Fraction,lru_cache=lru_cache);exec(compile(ast.Module(body=[func],type_ignores=[]),str(expr),'exec'),ns)
 jobs=[]
 for label,decisions in REVIEWS.items():
  prefix,name=label.split('_');base=ROOT/'runs'/('math_v3_components_20261027_01' if prefix=='GPT' else 'math_v3_components_deepseek_repair_20261027_01')/name
  a=json.loads((base/'artifact.json').read_text());props=json.loads((base/'test_proposals.json').read_text());assert len(props)==len(decisions)
  for i,(p,decision) in enumerate(zip(props,decisions)):
   problem=p['proposal']['problem'];params=None;answer=None;reason='Host semantic review independent of model labels.'
   if decision=='positive':
    if name=='F1':
     digits=[int(x) for x in re.search(r'\{([0-9, ]+)\}',problem).group(1).split(',')];length=int(re.search(r'(?:and|up to) (\d+)',problem).group(1))
     canonical='Choose between one and '+str(length)+' distinct digits from the set {'+', '.join(map(str,digits))+'} and arrange them without repetition. A leading zero is not allowed. How many prime numbers can be formed?'
     ref=mod.RestrictedDigitPrimeEnumerationTool.solve(canonical)
     if ref.status=='success':answer=str(ref.parameters['prime_count'])
     params=dict(digit_set=digits,max_length=length,forbid_leading_zero=True) if prefix=='GPT' else dict(digits=digits,max_length=length,allow_leading_zero=False)
     reason+=' Explicit distinct digits logically exclude reuse even if the phrase without repetition is missing. Leading zero handling is explicit or irrelevant because zero absent.'
    else:
     m=re.search(r'(?:expression |Consider )(\d+(?:\s+[+*\-/]\s+\d+)*)',problem);expression=m.group(1);nums=list(map(int,re.findall(r'\d+',expression)));ops=re.findall(r'[+*\-/]',expression)
     assert len(nums)==len(ops)+1 and all(op in ('+','-','*') for op in ops)
     answer=str(len(ns['_parenthesized_values'](tuple(nums),tuple(ops))))
     params=dict(operands=nums,operators=ops) if name=='F3' else dict(expression=expression)
     reason+=' Counting values denotes unique numerical values; the complete question fixes order and operations. Exact reference recursion is frozen before candidate generation.'
   elif decision=='negative':reason+=' Explicit mathematical target/operator/length or repetition is outside the frozen algorithm contract.'
   else:reason+=' Contradictory or incomplete constraints; no unique mathematical expectation certified. Refusal safety can be observed but not counted as math correctness.'
   jobs.append(dict(label=label,index=i,artifact=a,proposal=p['proposal'],problem_hash=fingerprint(problem),decision=decision,parameters=params,reference_answer=answer,reason=reason))
 save(out/'private/reviews.json',jobs)
 save(out/'freeze.json',dict(review_sha256=sha(out/'private/reviews.json'),script_sha256=sha(__file__),references={str(p):sha(p) for p in [path,expr]},reference_origin='Existing P0 private archived reference functions, not generated candidate; no new mathematical implementation; finite developer semantic review',no_gold_sent=True))
 runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),out/'worker.jsonl');results=[]
 for j in jobs:
  a=j['artifact'];observed=runner.run(a,PublicMathTask('proposal-'+j['problem_hash'][:16],j['proposal']['problem']))
  c=runner.solve(a,j['parameters']) if j['parameters'] is not None else None
  results.append(dict(label=j['label'],index=j['index'],observation=observed,independent_solve=c))
 save(out/'outputs_locked.json',results);save(out/'lock.json',dict(sha256=sha(out/'outputs_locked.json'),at=time.time()))
 def grade(v,a):
  x,y=normalized(v),normalized(a);return 'CORRECT' if x==y else 'WRONG' if x[0]==y[0]=='rational' else 'UNVERIFIED'
 for j,r in zip(jobs,results):
  r.update(decision=j['decision'],review_reason=j['reason'],computation='UNVERIFIED',combined='UNVERIFIED',applicability='UNVERIFIED')
  o=r['observation'];m=o['match']['status']
  if j['decision']=='negative':r['applicability']='FALSE_ACCEPT' if m=='MATCH' else 'CORRECT_REFUSAL' if m=='DECLINE' else m
  elif j['decision']=='positive':
   r['applicability']='MATCH' if m=='MATCH' else m
   c=r['independent_solve']
   if j['reference_answer'] is not None:
    r['computation']=grade(c['answer'],j['reference_answer']) if c['status']=='APPLIED' else c['status']
    r['combined']=grade(o['answer'],j['reference_answer']) if o['status']=='APPLIED' else o['status']
  else:r['applicability']='UNVERIFIED_ACCEPT' if m=='MATCH' else 'UNCERTAIN_REFUSAL'
 save(out/'scores.json',results);save(out/'summary.json',{label:{k:dict(collections.Counter(r[k] for r in results if r['label']==label)) for k in ('decision','computation','applicability','combined')} for label in REVIEWS})
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
