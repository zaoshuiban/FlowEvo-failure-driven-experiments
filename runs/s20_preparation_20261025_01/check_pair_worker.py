import sys,pathlib,tempfile,json
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import LearningStream,configure_worker
from test_s19_v2 import Provider,tasks,plan
from failure_evo.contracts import fingerprint
from s20_action_pair_preflight import reconstruct
configure_worker(e.read(R/'reports/s19_v2_acceptance/worker_environment.json'))
folder=P/'worker_batch_v2';folder.mkdir(exist_ok=True);(folder/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(folder/'tmp')
p=plan('s20-worker-batch');p.update(compile_protocol='s19-compile-envelope-v2',scheduler_protocol='evidence-diversity-v1',learning_evidence_protocol='learning-evidence-bundle-v1');p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
provider=Provider();r=e.ExperimentRunner(folder/'F',p,provider.factory);s=LearningStream(r,tasks(),batch_size=1);s.run(stop_after_batch=2)
assert not any(x['kind']=='ONLINE_LOCKED' for x in s.log.records());calls=dict(provider.calls)
r=e.ExperimentRunner(folder/'F',p,provider.factory,resume=True);s=LearningStream(r,tasks(),batch_size=1);s.run(stop_after_batch=2);assert calls==provider.calls
s.run();pairs=[]
for f in (r.folder/'branches').glob('*/*/workflow.json'):
 for h in e.read(f).get('hook_events',[]):
  if 'checkpoint_budget' in h:
   pair=reconstruct(h);assert pair['branches']['learned']['wire_sha256']==h['request_distinctness']['actual_sent_wire_sha256'];pairs.append(pair)
assert pairs
r.save();e.write(P/'worker_batch_acceptance.json',dict(passed=True,real_model_requests=0,real_worker=True,no_resend=True,not_locked_early=True,pairs=pairs,mock_calls=provider.calls))
print('PASS',len(pairs),'actual hook prefix reconstructions')
