import copy,unittest
from failure_evo.contracts import fingerprint
from test_math_cumulative_boundaries import Boundaries
from failure_evo.cluster_contract import *
from failure_evo.math_cumulative_learning import parse_relations

class Contract(Boundaries):
 def test_context_is_not_output_template(self):
  a=self.add(1)['id'];c=self.update([a]);ctx=ClusterContext.from_host(c).to_dict()
  self.assertEqual(set(ctx),{'reference_id','prior_hypothesis','prior_assessment'})
  ClusterContext.validate(ctx)
  with self.assertRaises(ValueError):ClusterProposal.validate(ctx)
  ctx['prior_hypothesis']['mechanism']='changed';self.assertNotEqual(c['hypothesis']['mechanism'],'changed')
 def test_valid_proposal_receives_without_permission(self):
  a=self.add(1)['id'];v=self.proposal([a]);parse_relations(v)
  c=self.m.associate(v,[a],[],1,fingerprint(v))[0];self.assertIs(c['verified'],False)
 def test_permission_fields_everywhere_rejected(self):
  a=self.add(1)['id']
  for key in PERMISSIONS:
   for val in [False,True,None]:
    for level in ['top','cluster','hypothesis','link']:
     v=self.proposal([a]);target={'top':v,'cluster':v['clusters'][0],'hypothesis':v['clusters'][0]['hypothesis'],'link':v['clusters'][0]['links'][0]}[level];target[key]=val
     with self.assertRaisesRegex(ValueError,'HOST_ONLY_FIELD'):parse_relations(v)
     with self.assertRaisesRegex(ValueError,'HOST_ONLY_FIELD'):self.m.associate(v,[a],[],1,fingerprint(v))
  self.assertFalse(self.m.state(1))
 def test_host_status_defaults_never_grant_permission(self):
  status=VerifiedCluster('host-id','host-version')
  self.assertFalse(status.verified or status.gate_passed or status.execution_authorized)
 def test_context_permissions_rejected(self):
  a=self.add(1)['id'];c=self.update([a]);ctx=ClusterContext.from_host(c).to_dict();ctx['verified']=False
  with self.assertRaises(ValueError):ClusterContext.validate(ctx)

if __name__=='__main__':unittest.main()
