"""Cluster-free deterministic selection, zero API."""
from test_association_lifecycle import Lifecycle
from failure_evo.evidence_retrieval import select
from failure_evo.contracts import canonical
import unittest

class Retrieval(Lifecycle):
 def pick(self,n,**kw):return select(self.m,n,max_records=kw.get('count',3),max_bytes=kw.get('size',22000))
 def test_without_clusters_old_and_new(self):
  a=self.add(1,'old')['id'];self.done([a],1);b=self.add(2,'new')['id']
  r=self.pick(2);self.assertEqual(r['selected_ids'],[b,a]);self.assertFalse(self.m.state(2));self.assertFalse(r['mechanism_established'])
 def test_different_original_preferred(self):
  a=self.add(1,'same')['id'];self.done([a],1)
  b=self.add(2,'different')['id'];self.done([b],2)
  c=self.add(3,'same')['id'];self.assertEqual(self.pick(3,count=2)['selected_ids'],[c,b])
 def test_deterministic_and_no_new_no_request(self):
  a=self.add(1)['id'];self.assertEqual(self.pick(1),self.pick(1));self.done([a],1)
  self.assertEqual(self.pick(1)['selected_ids'],[])
 def test_limits_and_all_candidates_logged(self):
  for n in range(1,5):self.add(n,'o'+str(n))
  r=self.pick(4,count=2);self.assertEqual(len(r['selected_ids']),2);self.assertEqual(len(r['candidates']),4)
  self.assertEqual(self.pick(4,size=2)['selected_ids'],[])
  self.assertLessEqual(r['conservative_input_token_upper'],r['max_bytes'])
 def test_future_exhausted_excluded(self):
  a=self.add(1)['id']
  for n in [1,2,3]:self.done([a],n)
  b=self.add(4)['id'];self.add(7)
  r=self.pick(4);self.assertEqual(r['selected_ids'],[b]);self.assertEqual(len(r['candidates']),2)

if __name__=='__main__':unittest.main()
