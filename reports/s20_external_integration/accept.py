import pathlib,sys,tempfile,json
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker,LearningStream
from test_s19_v2 import plan,tasks
from external_workflow_adapter import attach
from failure_evo.contracts import fingerprint
configure_worker(e.read(R/'reports/s19_v2_acceptance/worker_environment.json'))
tempfile.tempdir=str(R/'runs/s20_external_v2_20261025_01/tmp')
results=[]
for ds in ('apps','cc','lcb'):
 for arm in 'GMF':
  with tempfile.TemporaryDirectory() as tmp:
   ts=tasks(1);ts[0]['dataset']=ds;p=plan(ds+arm,learning=0);p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'});sent=[]
   def factory(ch):
    def send(wire):
     assert ch=='solve';sent.append(json.loads(wire));return dict(model='deepseek-flash',usage=dict(prompt_tokens=2,completion_tokens=2,total_tokens=4),choices=[dict(message=dict(content='```python\nprint(int(input()))\n```'),finish_reason='stop')])
    return send
   r=attach(e.ExperimentRunner(pathlib.Path(tmp)/'run',p,factory),ts);s=LearningStream(r,ts,arm=arm);
   try:s.run()
   except Exception:
    print(e.read(r.folder/'branches/fixture-0'/arm/'workflow.json')['events']);raise
   assert r.budgets['solve'].calls==1
   assert e.read(r.folder/'branches/fixture-0'/arm/'workflow.json')['status']=='PUBLIC_ACCEPTED'
   r.save();r2=attach(e.ExperimentRunner(r.folder,p,factory,resume=True),ts);LearningStream(r2,ts,arm=arm).run();assert len(sent)==1
   neg=r2.judge.run(ts[0]['task_id'],"print('INVALID')",ts[0]['public_cases']);assert not neg['passed']
   results.append(dict(dataset=ds,arm=arm,public_pass=True,negative_rejected=True,resume_no_replay=True,budget=r2.budgets['solve'].snapshot()))
e.write(R/'reports/s20_external_integration/acceptance.json',dict(passed=True,model_api_calls=0,scope='engineering stdio fixtures through real ExperimentRunner/LearningStream and Linux Worker, not 538 algorithm verification',rows=results))
print('PASS',len(results))
