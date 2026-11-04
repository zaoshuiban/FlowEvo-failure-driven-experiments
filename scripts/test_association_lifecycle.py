"""Zero API lifecycle regression using real cumulative evidence journals."""
from test_math_cumulative_boundaries import Boundaries
from failure_evo.contracts import fingerprint
import unittest

class Lifecycle(Boundaries):
 def done(self,ids,cutoff,outcome='REJECTED:format'):
  self.m.put(self.m.views,'ASSOCIATION_DONE',dict(evidence_ids=ids,cutoff=cutoff,outcome=outcome,path='fixture'),fingerprint([ids,cutoff]))
 def test_rejected_revisited_only_with_new_evidence(self):
  a=self.add(1,'one')['id'];self.assertEqual(self.m.association_states(1)[a]['state'],'NEW')
  self.done([a],1);self.assertEqual(self.m.association_states(1)[a]['state'],'ATTEMPTED')
  self.add(2,'two');self.assertEqual(self.m.association_states(2)[a]['state'],'RETRY_ELIGIBLE')
 def test_empty_cluster_is_not_linked(self):
  a=self.add(1)['id'];self.done([a],1,'ACCEPTED_UNVERIFIED')
  self.assertEqual(self.m.association_states(1)[a]['state'],'ATTEMPTED')
 def test_exhausted_preserves_evidence(self):
  a=self.add(1)['id']
  for n in [1,2,3]:self.done([a],n)
  self.add(4);self.assertEqual(self.m.association_states(4)[a]['state'],'EXHAUSTED');self.assertIn(a,self.m.facts(4))
 def test_linked_requires_actual_relation(self):
  a=self.add(1)['id'];self.update([a]);self.assertEqual(self.m.association_states(100)[a]['state'],'LINKED')
 def test_unrelated_not_linked(self):
  a=self.add(1)['id'];self.update([a],role='UNRELATED');self.done([a],100)
  self.assertEqual(self.m.association_states(100)[a]['state'],'ATTEMPTED')
 def test_no_future_revisit(self):
  a=self.add(1)['id'];self.done([a],1);self.add(5)
  self.assertEqual(self.m.association_states(2)[a]['state'],'ATTEMPTED')

if __name__=='__main__':unittest.main()
