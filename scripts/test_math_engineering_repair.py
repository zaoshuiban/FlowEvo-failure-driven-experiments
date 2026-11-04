"""Zero-API real Worker fixtures. Does not assert research success."""
import tempfile,sys,json
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE,save
from failure_evo.persistent_budget import PersistentBudget
def makebudget(path,run,ph,calls,cost,tools=0):
 return PersistentBudget(path,run_id=run,protocol_hash=ph,max_calls=calls,max_tokens=calls*73728,max_tools=tools,max_cost_microusd=cost,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=tools*20000,tool_milliseconds_upper=20000,wall_seconds=21600)
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.math_engineering_repair import *

GOOD='''import json
def solve(parameters):
    return str(parameters['n'] * 2)
def map_parameters(problem):
    try:
        p = json.loads(problem)
        if set(p) == {'n'} and type(p['n']) == int:
            return {'status':'MATCH','parameters':p,'reason':'fixture'}
    except Exception:
        pass
    return {'status':'DECLINE','parameters':{},'reason':'unsupported'}
def math_operator(context):
    m = map_parameters(context['problem'])
    if m['status'] != 'MATCH':
        return {'status':'DECLINED','reason':'unsupported'}
    return {'status':'APPLIED','answer':solve(m['parameters'])}
'''
BAD='''def math_operator(context):
    n=0
    def inner():
        nonlocal n
        n+=1
    return {'status':'APPLIED','answer':json.dumps(n)}
'''
def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks={}
 def denied(name,fn):
  try:fn()
  except (PermissionError,ValueError,FileExistsError):checks[name]=True
  else:checks[name]=False
 d=diagnose(BAD)
 checks['nonlocal_specific']=any(x.get('node')=='Nonlocal' for x in d['details'])
 checks['missing_import']=any(x.get('name')=='json' for x in d['details'])
 checks['source_not_rewritten']=digest(BAD)==d['static']['source_sha256']
 checks['comment_only']=version_change(GOOD,GOOD+'\n# comment')['classification']=='FORMAT_OR_DOCSTRING_ONLY'
 checks['math_change_substantive']=version_change(GOOD,GOOD.replace('* 2','* 3'))['classification']=='SUBSTANTIVE_OR_UNRESOLVED'
 checks['nonlocal_fix_not_format']=version_change(BAD,GOOD)['classification']=='SUBSTANTIVE_OR_UNRESOLVED'
 tasks=[dict(task_id='s',problem='{"n":2}')]
 req=engineering_request(GOOD,tasks)
 checks['no_feedback_or_gold']=set(req)=={'protocol','code','code_sha256','diagnostics','public_problems','contract','gold_exposed'}
 denied('reject_private_task_fields',lambda:engineering_request(GOOD,[dict(tasks[0],gold_answer='4')]))
 seen=[]
 for arm in ('T','F'):
  s=EngineeringRepairSession(out/arm)
  def sender(r):seen.append(r);return dict(code=GOOD,usage={'total_tokens':0},origin='MOCK')
  review=s.repair(BAD,tasks,sender,origin='MOCK')
  denied(arm+'_no_repeat',lambda:s.repair(BAD,tasks,sender,origin='MOCK'))
 checks['symmetric_wire']=seen[0]==seen[1]
 checks['raw_and_versions_saved']=all((out/a/'original.py').read_text()==BAD and (out/a/'revised.py').read_text()==GOOD for a in ('T','F'))
 s=EngineeringRepairSession(out/'empty');r=s.repair(GOOD,tasks,lambda r:{'code':'','usage':{}},origin='MOCK')
 checks['empty_is_delivery_not_unknown']=r['status']=='DELIVERY_REJECTED'
 s=EngineeringRepairSession(out/'unknown')
 try:s.repair(GOOD,tasks,lambda r:(_ for _ in ()).throw(TimeoutError('fixture')),origin='MOCK')
 except TimeoutError:pass
 denied('unknown_no_repeat',lambda:s.repair(GOOD,tasks,lambda r:{'code':GOOD},origin='MOCK'))
 b=makebudget(out/'budget.jsonl','engineering:repair',fingerprint(VERSION),0,0,tools=30)
 v=ComponentValidation(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),b,out/'validation.jsonl')
 a=dict(source_path=str(out/'T/revised.py'),code_sha256=digest(GOOD),operator_id='fixture',origin='MOCK')
 def c(i,n):return dict(task_id=i,problem=json.dumps({'n':n}),supported=True,parameters={'n':n},answer=str(2*n),review_status='INDEPENDENT_VERIFIED')
 negative=dict(task_id='negative',problem='No mathematical question.',supported=False,parameters={},answer=None,review_status='INDEPENDENT_VERIFIED')
 source=v.evaluate(a,[c('s',2)],'Source');design=v.evaluate(a,[c('d',3),negative],'Design')
 checks['three_validation_paths']=development_qualified([source,design])
 ready=freeze_for_gate(out/'gate_freeze.json',a,[source,design],out/'validation.jsonl')
 checks['no_auto_admission']=ready['experimental'] is False
 denied('gate_freeze_immutable',lambda:freeze_for_gate(out/'gate_freeze.json',a,[source,design],out/'validation.jsonl'))
 fake=dict(source,code_sha256='other')
 denied('forged_receipt',lambda:freeze_for_gate(out/'forged.json',a,[fake,design],out/'validation.jsonl'))
 (out/'bad.py').write_text(GOOD.replace('* 2','* 3'));bad=dict(a,source_path=str(out/'bad.py'),code_sha256=digest((out/'bad.py').read_text()))
 wrong=v.evaluate(bad,[c('w',4)],'Source')
 checks['algorithm_error_separate']=wrong['rows'][0]['parameter_correct'] and not wrong['rows'][0]['computation_correct']
 denied('bad_compute_no_gate',lambda:freeze_for_gate(out/'badgate.json',bad,[wrong,design],out/'validation.jsonl'))
 (out/'mapping.py').write_text(GOOD.replace("'parameters':p", "'parameters':{'n':1}"))
 mapped=dict(a,source_path=str(out/'mapping.py'),code_sha256=digest((out/'mapping.py').read_text()))
 m=v.evaluate(mapped,[c('map',4)],'Source')['rows'][0]
 checks['mapping_error_separate']=m['computation_correct'] and not m['parameter_correct'] and not m['combined_correct']
 (out/'T/revised.py').write_text(GOOD+'\n# altered')
 denied('source_mutation_denied',lambda:v.call(a,'solve',[{'n':2}]))
 save(out/'summary.json',dict(checks=checks,passed=sum(checks.values()),total=len(checks),real_model_calls=0,engineering_only=True))
 print(json.dumps(checks,indent=2));assert all(checks.values())
if __name__=='__main__':main()
