"""Replay policy parity on actual fixed historical responses, plus CLI acceptance."""
import hashlib,json,pathlib,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1];B=R.parent
PROJECT=R/'implementation/FlowEvo'
if not PROJECT.exists():PROJECT=B.parents[1]/'FlowEvo'
sys.path.insert(0,str(PROJECT/'src'))
from failure_evo import Budget,Controller,Fingerprint
from failure_evo.contracts import public_schema
def read(p):return json.loads(p.read_text())
def main():
 sys.path.insert(0,str(PROJECT/'tests'));import test_failure_evo
 stream=__import__('io').StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_failure_evo))
 (R/'framework_unittest.log').write_text(stream.getvalue());assert result.wasSuccessful()
 m=read(R/'review_manifest.json');rows=[];provider_replays=0
 for t in m['tasks']:
  tid=t['task_id'];raw=read(R/'source/tasks'/(tid+'.json'));statuses=[]
  for a in t['historical_programs']:
   base=read(R/'verdicts'/tid/(a['stage']+'.json'));stress=R/'stress_verdicts_v2'/tid/(a['stage']+'.json');extra=read(stress) if stress.exists() else None
   statuses.append(extra['status'] if base['passed'] and extra is not None and not extra['passed'] else base['status'])
  expected=next((i for i,s in enumerate(statuses) if s=='PASS'),None);n=(expected+1 if expected is not None else len(statuses));position=[-1]
  def provider(request):
   position[0]+=1;a=t['historical_programs'][position[0]];return {'code':(R/a['source_path']).read_text(),'model':'deepseek-flash','usage':{'total_tokens':0}}
  def public_evaluator(task,code):return {'visibility':'public','status':'PUBLIC_PASS' if statuses[position[0]]=='PASS' else statuses[position[0]]}
  fp=Fingerprint('FlowEvo-clean-S1','public_suite_plus_stress_v2','deepseek-flash','pinned_sandbox','fixed-response-policy-replay')
  out=Controller(provider,public_evaluator,fp,clock=lambda:1).solve(raw,Budget(max_tokens=1000000,clock=lambda:0));assert len(out['events'])==n
  assert (out['selected']['stage'] if out['selected'] else None)==(t['historical_programs'][expected]['stage'] if expected is not None else None)
  for e in out['events']:
   q=json.dumps(e['request']);assert 'input_output' not in q and 'hidden_tests' not in q and 'future_trace' not in q
  provider_replays+=n;rows.append({'task_id':tid,'checked_stages':n,'selected_public_stage':out['selected']['stage'] if out['selected'] else None,'status':'POLICY_PARITY_PASS'})
 output={'status':'PASS','unit_tests':result.testsRun,'unit_failures':len(result.failures)+len(result.errors),'real_task_policy_replays':len(rows),'replayed_provider_responses':provider_replays,'new_model_calls':0,'new_model_tokens':0,
         'scope':'stage/retention/stop parity conditional on fixed saved responses; not a fresh generation or causal performance experiment','rows':rows}
 (R/'framework_acceptance.json').write_text(json.dumps(output,indent=2));(R/'public_view_schema.json').write_text(json.dumps(public_schema(),indent=2));print('FRAMEWORK PASS',result.testsRun,'unit tests;',len(rows),'real fixed-response policy replays')
if __name__=='__main__':main()
