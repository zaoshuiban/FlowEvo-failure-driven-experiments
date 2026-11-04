"""Fault injection and read-only historical response replay, no paid requests."""
import sys,copy,json
from pathlib import Path
from test_math_engineering_repair import GOOD,BAD,makebudget
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.math_engineering_repair import *
from failure_evo.autonomous_mvp import FrozenLinuxBackend

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'runs/math_reliability_v2_20261031_01'
def main():
 OUT.mkdir(exist_ok=False);checks={}
 def check(name,value):checks[name]=bool(value)
 def denied(name,fn):
  try:fn()
  except (ValueError,PermissionError,FileExistsError):checks[name]=True
  else:checks[name]=False
 parent=ROOT/'runs/math_symmetric_repair_20261031_01'
 hashes={str(p):sha(p) for p in parent.rglob('*') if p.is_file()}
 for name,r in [('list',[]),('truncated',dict(code=GOOD,finish_reason='length')),
   ('invalid',dict(code=GOOD,delivery_status='CONTRACT_INVALID')),('size',dict(code='a'*65537))]:
  result=EngineeringRepairSession(OUT/name).repair(GOOD,[],lambda q,r=r:r,origin='MOCK')
  check('reject_'+name,result['status']=='DELIVERY_REJECTED' and not (OUT/name/'revised.py').exists())
  check('preserve_raw_'+name,(OUT/name/'response.json').exists())
  denied('no_resend_'+name,lambda:EngineeringRepairSession(OUT/name).repair(GOOD,[],lambda q:{'code':GOOD},origin='MOCK'))
 replays=[]
 for path in sorted(parent.glob('*/repair/response.json')):
  r=json.loads(path.read_text());rejection=receive_source(r,'DEEPSEEK')
  replays.append(dict(path=str(path),response_sha256=sha(path),rejection=rejection))
 check('six_original_raw_sources_accepted',len(replays)==6 and all(x['rejection'] is None for x in replays))
 r=json.loads(next(parent.glob('*/repair/response.json')).read_text())
 changed=copy.deepcopy(r);changed['code']+='\n# injected'
 check('code_provenance_tamper',receive_source(changed,'DEEPSEEK')=='SOURCE_PROVENANCE_MISMATCH')
 changed=copy.deepcopy(r);changed['raw_response']['id']='changed'
 check('raw_hash_tamper',receive_source(changed,'DEEPSEEK')=='RESPONSE_PROVENANCE_MISMATCH')
 check('partial_real_response_rejected',receive_source({'code':GOOD},'DEEPSEEK')=='INCOMPLETE_DELIVERY')
 check('missing_import_blocks_components',not diagnose(GOOD.replace('import json\n',''))['component_ready'])
 check('duplicate_solve_blocks',not diagnose(GOOD+'\ndef solve(parameters):\n    return "0"\n')['component_ready'])
 check('rebound_entry_blocks',not diagnose(GOOD+'\nsolve = 3\n')['component_ready'])
 d=OUT/'worker';d.mkdir();budget=makebudget(d/'budget.jsonl','engineering:reliability-v2',fingerprint(VERSION),0,0,tools=50)
 def art(name,code):
  p=d/(name+'.py');p.write_text(code);return dict(source_path=str(p),code_sha256=digest(code),operator_id=name,origin='MOCK')
 a=art('good',GOOD);v=ComponentValidation(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),budget,d/'validation.jsonl')
 def case(t,n=2):return dict(task_id=t,problem=json.dumps({'n':n}),supported=True,parameters={'n':n},answer=str(n*2),review_status='INDEPENDENT_VERIFIED')
 neg=dict(task_id='neg',problem='No math.',supported=False,parameters={},answer=None,review_status='INDEPENDENT_VERIFIED')
 denied('entry_allowlist',lambda:v.call(a,'other',[]))
 denied('case_duplicate_preflight',lambda:v.evaluate(a,[case('x'),case('x')],'Source'))
 denied('untrusted_review_preflight',lambda:v.evaluate(a,[dict(case('x'),review_status='UNVERIFIED')],'Source'))
 denied('support_string_rejected',lambda:v.evaluate(a,[dict(case('x'),supported='false')],'Source'))
 check('bad_cases_spend_zero_worker',budget.snapshot()['tool_calls']==0)
 source=v.evaluate(a,[case('s')],'Source')
 denied('source_repeat_blocked',lambda:v.evaluate(a,[case('s')],'Source'))
 denied('role_id_overlap',lambda:v.evaluate(a,[case('s',3)],'Design'))
 denied('role_problem_overlap',lambda:v.evaluate(a,[case('new-id',2)],'Design'))
 design=v.evaluate(a,[case('d',3),neg],'Design')
 check('valid_development_qualifies',development_qualified([source,design]))
 check('duplicate_receipt_fails',not development_qualified([source,design,design]))
 old=copy.deepcopy(source);old['protocol']='symmetric-math-engineering-repair-v1'
 check('old_receipt_no_inheritance',not development_qualified([old,design]))
 # bool and int compare equal in Python; parameter mapping must distinguish them.
 boolean=art('boolean',GOOD.replace("'parameters':p","'parameters':{'n':True}"))
 row=v.evaluate(boolean,[case('b',1)],'Source')['rows'][0]
 check('boolean_is_not_integer_mapping',row['parameter_correct'] is False and row['computation_correct'])
 check('parameter_diagnosis_category','PARAMETER_MISMATCH' in row['failure_categories'])
 # Correct final answer does not justify a contradictory mapping decision.
 bypass=art('bypass',GOOD.replace("if m['status'] != 'MATCH':","if False:").replace("solve(m['parameters'])","'4'"))
 row=v.evaluate(bypass,[dict(case('bypass'),problem='unsupported wording')],'Source')['rows'][0]
 check('mapping_decline_compute_bypass_detected',row['combined_correct'] and not row['routing_consistent'])
 dirty=art('dirty',GOOD.replace("'status':'DECLINE','parameters':{}","'status':'DECLINE','parameters':{'n':3}"))
 row=v.evaluate(dirty,[dict(neg,task_id='dirty')],'Design')['rows'][0]
 check('refusal_parameters_invalid',not row['mapping_valid'])
 # Exception category remains execution, not ordinary mathematical incorrectness.
 error=art('error',GOOD.replace("return str(parameters['n'] * 2)","return str(1 // 0)"))
 row=v.evaluate(error,[case('error')],'Source')['rows'][0]
 check('runtime_error_preserved',row['computation']['status']!='OK' and row['end_to_end']['status']=='ERROR')
 check('execution_not_math_diagnosis','COMPUTATION_EXECUTION_ERROR' in row['failure_categories'] and 'COMPUTATION_MISMATCH' not in row['failure_categories'])
 # A crash after role reservation blocks an implicit rerun.
 bad=art('bad',BAD)
 denied('static_block_before_execution',lambda:v.evaluate(bad,[case('fail')],'Source'))
 denied('failed_attempt_not_restarted',lambda:v.evaluate(bad,[case('fail')],'Source'))
 check('history_unchanged',all(sha(p)==h for p,h in hashes.items()))
 save(OUT/'summary.json',dict(protocol=VERSION,checks=checks,passed=sum(checks.values()),total=len(checks),paid_calls=0,
   historical_response_replay=replays,budget=budget.snapshot(),source_hashes={p:sha(ROOT/p) for p in ['FlowEvo/src/failure_evo/math_engineering_repair.py','scripts/test_math_reliability_v2.py']}))
 print(json.dumps(checks,indent=2));assert all(checks.values())
if __name__=='__main__':main()
