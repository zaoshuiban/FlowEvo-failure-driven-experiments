"""Minimal public counterexample and deletion-only counterfactual, no generation model."""
import ast,difflib,hashlib,json,pathlib,random
from legal_suite import R,B
from input_audit import audit
from replay import evaluate,read,write,sha
def main():
 tid='taco_0966';task=next(t for t in read(R/'review_manifest.json')['tasks'] if t['task_id']==tid);a=next(x for x in task['historical_programs'] if x['stage']=='l1');source=R/a['source_path'];original=source.read_text();tree=ast.parse(original);solve=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='solve');prepass=next(n for n in solve.body if isinstance(n,ast.For));lines=original.splitlines(True);patched=''.join(lines[:prepass.lineno-1]+lines[prepass.end_lineno:]);assert patched!=original and original.count('for _ in range(t):')==2 and patched.count('for _ in range(t):')==1
 d=R/'counterfactuals'/tid;d.mkdir(parents=True,exist_ok=True);(d/'original.py').write_text(original);(d/'patched.py').write_text(patched);(d/'minimal.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),patched.splitlines(True),fromfile='original.py',tofile='patched.py')))
 minimal={'input':'2\n1\n0\n4\n1\n0\n0\n','expected':'1\n1','comparison':'tokens','contract_scope':'LEGAL_STATEMENT_DOMAIN','provenance':'public hand-minimized input from independently generated multi-test failure, not a hidden test'}
 cases=[minimal];rng=random.Random(20261021)
 for i in range(64):
  count=rng.randint(2,10);parts=[str(count)];expected=[]
  for j in range(count):
   n=rng.randint(1,12);values=[rng.randrange(32) for _ in range(n)];mask=rng.randrange(32);parts.extend([str(n),' '.join(map(str,values)),str(mask)]);expected.append(str(sum(((u^v)&mask)==0 for u in values for v in values)))
  cases.append({'input':'\n'.join(parts)+'\n','expected':'\n'.join(expected),'comparison':'tokens','contract_scope':'LEGAL_STATEMENT_DOMAIN','provenance':'new independent public multi-case generator seed20261021; literal ordered-pair oracle'})
 for c in cases:audit(tid,c['input'])
 write(d/'public_validation_cases.json',cases)
 first=evaluate(tid,d/'original.py',[minimal]);fixed=evaluate(tid,d/'patched.py',cases+read(R/'public_suite.json')['cases'][tid]+read(R/'stress_suite_v2.json')['cases'][tid]);assert first['status']=='RUNTIME_ERROR' and fixed['passed']
 near=[{'input':'1\n1\n0\n4\n','expected':'1','comparison':'tokens'},{'input':'2\n1\n0\n3\n1\n0\n0\n','expected':'1\n1','comparison':'tokens'}]
 near_result=evaluate(tid,d/'original.py',near);assert near_result['passed']
 case_id='public_taco0966_multicase_cursor_min';actual=first['failures'][0]['actual'];assert 'IndexError' in actual['stderr']
 write(d/'legal_case.json',{**minimal,'case_id':case_id,'visibility':'public','legal_verified':True,'validator':'input_audit.audit','bounds':'T=2, each N=1,A=0; X=4 and0, all in declared ranges'})
 write(d/'oracle.json',{'case_id':case_id,'independent':True,'method':'each testcase has exactly one ordered pair (1,1); XOR=0 and 0&X=0 for any legal X','expected':'1\n1'})
 write(d/'original_run.json',{'case_id':case_id,'code_sha256':sha(d/'original.py'),'status':first['status'],'exception_class':'IndexError','expected':'1\n1','actual':actual,'replay':first})
 write(d/'patched_run.json',{'case_id':case_id,'code_sha256':sha(d/'patched.py'),'status':'PASS','tests_passed':fixed['tests_passed'],'original_witness_passed':True,'replay':fixed})
 write(d/'review.json',{'mechanism_verified':True,'reviewer':'Codex manual source/contract review plus deterministic sandbox replay','violated_invariant':'the input cursor must consume exactly N and A and X for each case once; an obsolete preliminary parsing loop omits X and interprets it as the next N','minimal_counterfactual':'delete only the obsolete first top-level parsing loop; retain correct second parser and frequency-squared algorithm','near_miss_original_pass':near_result,'scope':'implementation defect in one historical l1; not evidence of stable cross-task failure'})
 write(d/'verification.json',{'original_minimal_status':first['status'],'patched_status':fixed['status'],'patched_cases':fixed['tests_passed'],'near_miss_original_cases':near_result['tests_passed'],'new_model_calls':0})
 print('WITNESS',tid,first['status'],'PATCHED PASS',fixed['tests_passed'],'NEAR_MISS PASS',near_result['tests_passed'],flush=True)
if __name__=='__main__':main()
