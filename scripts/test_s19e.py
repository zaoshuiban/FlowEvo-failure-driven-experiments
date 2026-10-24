"""Real-input read-only checks and new-entry mock transport acceptance; zero API."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run_workflow_v2 as e
from run_learning_stream import LearningStream
from test_s19_v2 import Provider,FakeJudge,plan,tasks
from replay_s19e import JOBS,SOURCE_JOB,rows,read
from failure_evo import learning_evidence_bundle as leb
from failure_evo.contracts import fingerprint
from failure_evo.workflow_protocol_v2 import prepare

SOURCE=e.ROOT/'runs/s19_stream20_20261024_01'
class Tests(unittest.TestCase):
 def material(self,i=2):
  material=json.loads(read(SOURCE/'jobs'/JOBS[i]/'0-messages.json')[1]['content'])
  start=next(r for r in rows(SOURCE/'hypotheses.jsonl') if r['kind']=='JOB_STARTED' and r['payload']['job_id']==JOBS[i])
  facts={r['payload']['event_id']:r['payload'] for r in rows(SOURCE/'evidence_F.jsonl') if r['kind']=='FAILURE_FACT'}
  return material['source_packets'],facts,start['payload'],start['at']
 def test_three_sendable_diversity_and_permutation(self):
  for i in range(3):
   ps,fs,j,t=self.material(i);b=leb.build(ps,fs,j,cutoff=t)
   self.assertEqual(b,leb.build(list(reversed(ps)),fs,j,cutoff=t))
   self.assertLessEqual(prepare(leb.messages(b),json_output=True).input_upper,32768)
   self.assertEqual(set(b['task_ids']),{p['task_id'] for p in ps})
   self.assertEqual(set(b['task_ids']),{p['task_id'] for p in b['representatives']})
   self.assertEqual(len(b['events']),len(ps));self.assertTrue(b['symptom_group'])
   self.assertTrue(all(r['code']['is_fragment'] for r in b['representatives']))
 def test_real_packets_pass_fresh_persistent_reservation(self):
  from failure_evo.persistent_budget import PersistentBudget
  config=read(SOURCE/'plan.json')['budgets']['learning']
  with tempfile.TemporaryDirectory() as tmp:
   budget=PersistentBudget(Path(tmp)/'mock-reservations.jsonl',run_id='zero-api-reservation-check',protocol_hash='engineering',**config)
   for i in range(3):
    ps,fs,j,t=self.material(i);p=prepare(leb.messages(leb.build(ps,fs,j,cutoff=t)),json_output=True)
    key=budget.reserve(p.input_upper,p.output_upper,request_id=j['job_id'],request_hash=p.sha256)
    self.assertTrue(key)
   self.assertEqual(budget.calls,3)
   # Isolated engineering ledger discarded; no provider, settlement or old-run mutation.
 def test_temporal_and_binding(self):
  ps,fs,j,t=self.material()
  for mutation in ('future','hash','private','missing'):
   a=copy.deepcopy(ps);f=copy.deepcopy(fs)
   if mutation=='future':f[a[0]['event_id']]['available_from']=t+1
   if mutation=='hash':a[0]['code']+='broken'
   if mutation=='private':a[0]['feedback']['hidden_score']='PRIVATE_SENTINEL'
   if mutation=='missing':a.pop()
   with self.assertRaises(ValueError):leb.build(a,f,j,cutoff=t)
 def test_representation_limit_is_finite(self):
  ps,fs,j,t=self.material()
  with patch.object(leb,'MAX_BUNDLE_BYTES',100):
   with self.assertRaises(leb.EvidenceRepresentationLimit) as c:leb.build(ps,fs,j,cutoff=t)
  self.assertEqual(c.exception.reason,'EVIDENCE_REPRESENTATION_LIMIT')
 def diagnosis(self,slot=0):
  report=read(SOURCE/'assessments'/f'{SOURCE_JOB}-{slot}.json')
  packet=read(SOURCE/'public_packets'/f"{report['source_event_id']}.json")
  rule=read(SOURCE/'jobs'/SOURCE_JOB/'0-normalization.json')['normalized']['rule']
  return report,packet,rule
 def test_source_diagnosis_and_truncation(self):
  for slot in (0,1):
   r,p,rule=self.diagnosis(slot);d=leb.diagnostic(r,p,rule,report_ref='assessments/source.json',observed_at=10,cutoff=10)
   self.assertEqual(d['truncated'],slot==1);self.assertIn('remaining_budget',d)
   self.assertNotIn('stderr',json.dumps(d));self.assertNotIn('response',d)
   self.assertEqual(d['before_program_sha256'],p['candidate_sha256'])
   if slot==0:self.assertIn('IndexError',json.dumps(d))
   else:self.assertEqual(d['delivery_state']['structural_status'],'NO_COMPLETE_CODE')
 def test_diagnostic_private_and_time_rejected(self):
  for mutation in ('hidden_case','private_case','cost','budget','future'):
   r,p,rule=self.diagnosis()
   if mutation=='hidden_case':r['after']['cases'][0]['input']='PRIVATE_SENTINEL'
   if mutation=='private_case':r['after']['cases'][0]['visibility']='private'
   if mutation=='cost':r['cost']['tokens']={'hidden_score':1}
   if mutation=='budget':r['validation_budget_after']['hidden_score']=1
   with self.assertRaises(ValueError):leb.diagnostic(r,p,rule,report_ref='r',observed_at=11 if mutation=='future' else 10,cutoff=10)
 def test_new_entry_revision_and_hook_receipts(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   p=plan('s19e-mock');p.update(learning_evidence_protocol=leb.VERSION,compile_protocol='s19-compile-envelope-v2',scheduler_protocol='evidence-diversity-v1');p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
   provider=Provider();runner=e.ExperimentRunner(Path(tmp)/'stream',p,provider.factory)
   stream=LearningStream(runner,tasks(),batch_size=1);stream.run()
   bundles=[read(f)['bundle'] for f in runner.folder.glob('jobs/*/*-evidence-bundle.json')]
   self.assertTrue(bundles);self.assertTrue(any(b['functional_evidence'] for b in bundles))
   for f in runner.folder.glob('jobs/*/*-messages.json'):
    m=read(f);self.assertIn('learning_evidence_bundle',json.loads(m[1]['content']));self.assertNotIn('source_packets',json.loads(m[1]['content']))
   hooks=[h for f in runner.folder.glob('branches/*/*/workflow.json') for h in read(f).get('hook_events',[])]
   audited=[h['request_distinctness'] for h in hooks if h.get('request_distinctness')]
   self.assertTrue(audited)
   self.assertTrue(all(a['actual_sent_wire_sha256']==a['learned']['wire_sha256'] for a in audited))
   with stream.memory._transaction() as (rs,_):self.assertTrue(any(x.get('decision')=='SUSPEND' for x in rs))
 def test_preflight_before_reservation(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   p=plan('limit');p['learning_evidence_protocol']=leb.VERSION;p['compile_protocol']='s19-compile-envelope-v2';p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
   provider=Provider();runner=e.ExperimentRunner(Path(tmp)/'s',p,provider.factory)
   with patch.object(leb,'MAX_BUNDLE_BYTES',100):LearningStream(runner,tasks(1),batch_size=1).run()
   self.assertEqual(provider.calls['learning'],0);self.assertEqual(provider.calls['validation'],0)
   self.assertEqual(runner.budgets['learning'].snapshot()['remaining_calls'],4)
if __name__=='__main__':unittest.main()
