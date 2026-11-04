import copy,unittest
from test_math_cumulative_boundaries import Boundaries
from failure_evo.evidence_links import *
from failure_evo.contracts import fingerprint
class Links(Boundaries):
 def test_multiple_quotes_one_event(self):
  a=self.add(1)['id'];v=self.proposal([a]);l=v['clusters'][0]['links'][0]
  l['relation']='UNCERTAIN';l['quote_spans']=[l.pop('evidence_quote'),'The answer is 9']
  c=self.m.associate(v,[a],[],1,fingerprint(v))[0]
  self.assertEqual(c['links'][a]['relation'],'POSSIBLE');self.assertEqual(len(c['links'][a]['quote_spans']),2)
 def test_conflict_atomic_diagnostic(self):
  a=self.add(1)['id'];v=self.proposal([a]);c=v['clusters'][0];c['links'].append(dict(c['links'][0],relation='COUNTEREXAMPLE'))
  with self.assertRaises(LinkConflict) as ex:self.m.associate(v,[a],[],1,fingerprint(v))
  self.assertEqual(ex.exception.diagnostic['relations'],['SUPPORT','COUNTEREXAMPLE']);self.assertFalse(self.m.state(1))
 def test_revision_preserves_quotes_and_hypothesis(self):
  a=self.add(1)['id'];v=self.proposal([a]);old=v['clusters'][0]['links'][0];v['clusters'][0]['links'].append(dict(old,evidence_quote='The answer is 9',relation='COUNTEREXAMPLE'))
  new=copy.deepcopy(v);new['clusters'][0]['links']=[dict(evidence_id=a,relation='UNCERTAIN',quote_spans=[old['evidence_quote'],'The answer is 9'],reason='Conflicting claims',new_information=True)]
  validate_revision(v,new);self.m.associate(new,[a],[],1,fingerprint(new))
  new['clusters'][0]['links'][0]['quote_spans'].pop()
  with self.assertRaises(ValueError):validate_revision(v,new)
 def test_each_quote_grounded(self):
  a=self.add(1)['id'];v=self.proposal([a]);l=v['clusters'][0]['links'][0];l['relation']='SUPPORTS';l['quote_spans']=[l.pop('evidence_quote'),'invented']
  with self.assertRaisesRegex(ValueError,'quote_spans'):self.m.associate(v,[a],[],1,fingerprint(v))
 def test_revision_path_once_and_replay(self):
  import json
  from types import SimpleNamespace
  from failure_evo.math_cumulative_learning import CumulativeLearner
  from failure_evo.evidence import EvidenceStore
  a=self.add(1)['id'];old=self.proposal([a]);link=old['clusters'][0]['links'][0]
  old['clusters'][0]['links'].append(dict(link,relation='COUNTEREXAMPLE'))
  new=copy.deepcopy(old);new['clusters'][0]['links']=[dict(evidence_id=a,relation='UNCERTAIN',quote_spans=[link['evidence_quote']],reason='Conflict unresolved',new_information=True)]
  calls=[]
  class Compiler:
   events=EvidenceStore(self.root/'mock_compiler.jsonl')
   def request(inner,*args,**kwargs):calls.append(args);return {'specification':json.dumps(new)}
  learner=CumulativeLearner.__new__(CumulativeLearner);learner.memory=self.m;learner.arm='F'
  learner.cfg={'comparison':'workflow','output_upper':8192};learner.stream=SimpleNamespace(health=lambda:None)
  learner.capacity=lambda *args:True
  learner._provider=lambda *args:(SimpleNamespace(config={'run_id':'mock'},snapshot=lambda:{'calls':1}),SimpleNamespace(),Compiler())
  job={'family_id':'original','association_input':{}}
  result=learner.repair_relation_conflict(self.root/'job',job,old,{'code':'fixture'},[a],[],1)
  self.assertEqual(result,'ACCEPTED_UNVERIFIED_AFTER_RELATION_REVISION')
  self.assertEqual(learner.repair_relation_conflict(self.root/'job',job,old,{'code':'fixture'},[a],[],1),result)
  self.assertEqual(len(calls),1)
if __name__=='__main__':unittest.main()
