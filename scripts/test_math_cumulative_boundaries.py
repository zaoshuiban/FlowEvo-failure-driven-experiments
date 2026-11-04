"""Focused security/novelty boundaries, no model/Worker calls."""
import tempfile,copy,json,unittest
from pathlib import Path
from failure_evo.math_cumulative import *
from math_candidate_mock import assessment
from code_math.no_gold import PublicMathTask

class Boundaries(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.m=CumulativeMemory(self.root,'F');self.q=CumulativeQueue(self.root/'queue.jsonl')
 def tearDown(self):self.tmp.cleanup()
 def add(self,n,original='UNKNOWN',status='CONFIRMED_WRONG',finish='stop'):
  t=PublicMathTask('t'+str(n),'Public task '+str(n));l=dict(task_id=t.task_id,sequence=n,final_output='The answer is 9',responses=[dict(text='The answer is 9',finish_reason=finish,usage={},model='MOCK')]);l['locked_sha256']=fingerprint(l)
  return self.m.ingest(t,l,dict(status=status,locked_sha256=l['locked_sha256']),original,n)
 def proposal(self,ids,cid='NEW',role='SUPPORT',new=True,executable=True):
  facts=self.m.facts(100)
  return dict(descriptions=[dict(evidence_id=i,task_structure='shape',observable_symptom='observed',possible_cause='unverified',possible_correction='candidate',uncertainty='unknown') for i in ids],clusters=[dict(cluster_id=cid,hypothesis=dict(mechanism='candidate',uncertainty='unknown',applicability='unknown',exclusions='unknown',input_output='unknown'),assessment=assessment(ids,decision='GENERATE' if executable else 'NEEDS_SPECIFICATION'),links=[dict(evidence_id=i,relation=role,reason='hypothesis only',evidence_quote=facts[i]['task']['problem'],new_information=new) for i in ids])])
 def update(self,ids,cid='NEW',**kw):
  v=self.proposal(ids,cid,**kw);return self.m.associate(v,ids,[] if cid=='NEW' else [cid],100,fingerprint(v))[0]
 def test_no_false_failure(self):
  for n,status in enumerate(['CONFIRMED_CORRECT','UNVERIFIED','TRUNCATED','INFRASTRUCTURE_MISSING'],1):self.assertIsNone(self.add(n,status=status))
  self.assertFalse(self.m.facts(100))
 def test_truncated_wrong_rejected(self):
  with self.assertRaises(PermissionError):self.add(1,finish='length')
 def test_single_unknown_source_exploration(self):
  a=self.add(1);self.update([a['id']]);j=self.q.schedule(self.m,100,budget_available=True)[0]
  self.assertEqual(j['decision'],'EXPLORE_SINGLE_WITNESS');self.assertEqual(j['priority_basis']['confirmed_originals'],0)
 def test_same_evidence_no_relaunch(self):
  a=self.add(1);c=self.update([a['id']]);j=self.q.schedule(self.m,100,budget_available=True)[0];self.q.start(j);self.q.finish(j,{})
  self.update([a['id']],c['cluster_id']);self.assertEqual(self.q.schedule(self.m,100,budget_available=True),[])
 def test_same_original_duplicate_not_information(self):
  a=self.add(1,'orig');c=self.update([a['id']]);j=self.q.schedule(self.m,100,budget_available=True)[0];self.q.start(j);self.q.finish(j,{})
  b=self.add(2,'orig');self.update([b['id']],c['cluster_id'],new=False)
  self.assertEqual(self.q.schedule(self.m,100,budget_available=True),[])
 def test_counterexample_triggers_and_retained(self):
  a=self.add(1,'orig');c=self.update([a['id']]);j=self.q.schedule(self.m,100,budget_available=True)[0];self.q.start(j);self.q.finish(j,{})
  b=self.add(2,'orig');c=self.update([b['id']],c['cluster_id'],role='COUNTEREXAMPLE',new=False)
  self.assertEqual(len(self.q.schedule(self.m,100,budget_available=True)),1)
  self.assertEqual(self.m.bundle(c,100)['evidence'][0]['relation'],'COUNTEREXAMPLE')
  with self.assertRaises(ValueError):self.m.bundle(c,100,100)
 def test_multi_membership_and_unknown(self):
  a=self.add(1);v=self.proposal([a['id']]);v['clusters']*=2
  self.m.associate(v,[a['id']],[],1,fingerprint(v));self.assertEqual(len(self.m.state(1)),2)
  b=self.add(2);v=self.proposal([b['id']]);v['clusters']=[];self.m.associate(v,[b['id']],[],2,fingerprint(v));self.assertEqual(len(self.m.state(2)),2)
 def test_invented_quote_reject_atomic(self):
  a=self.add(1);v=self.proposal([a['id']]);v['clusters'][0]['links'][0]['evidence_quote']='not in input'
  with self.assertRaises(ValueError):self.m.associate(v,[a['id']],[],1,fingerprint(v))
  self.assertFalse(self.m.state(1));self.assertFalse(self.m.views.records())
 def test_future_rejected(self):
  a=self.add(2);v=self.proposal([a['id']])
  with self.assertRaises(PermissionError):self.m.associate(v,[a['id']],[],1,fingerprint(v))
 def test_metadata_cannot_verify_or_authorize(self):
  a=self.add(1);v=self.proposal([a['id']]);v['clusters'][0]['verified']=True
  with self.assertRaises(ValueError):self.m.associate(v,[a['id']],[],1,fingerprint(v))
 def test_no_budget_preserves_queue(self):
  a=self.add(1);self.update([a['id']]);self.assertFalse(self.q.schedule(self.m,100,budget_available=False));self.assertEqual(len(self.q.schedule(self.m,100,budget_available=True)),1)
 def test_independent_queue_matrix(self):
  for cause in ['SUPPORTED','SUSPECTED','UNSUPPORTED']:
   for decision in ['GENERATE','NEEDS_SPECIFICATION','NOT_GENERATABLE']:
    path=self.root/(cause+decision);self.m=CumulativeMemory(path,'F');self.q=CumulativeQueue(path/'queue.jsonl')
    a=self.add(1);v=self.proposal([a['id']]);v['clusters'][0]['assessment']=assessment([a['id']],status=cause,decision=decision)
    self.m.associate(v,[a['id']],[],1,fingerprint(v))
    self.assertEqual(bool(self.q.schedule(self.m,1,budget_available=True)),decision=='GENERATE')
 def test_active_unknown_blocks(self):
  a=self.add(1);self.update([a['id']]);j=self.q.schedule(self.m,100,budget_available=True)[0];self.q.start(j)
  with self.assertRaises(RuntimeError):self.q.schedule(self.m,100,budget_available=True)
if __name__=='__main__':unittest.main()
