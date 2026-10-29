import unittest,tempfile,json,sys
from pathlib import Path
from run_math_v34 import ROOT,WORKER,IMAGE,Adapter,guard,check_semantics
from failure_evo.contracts import fingerprint
from failure_evo.semantic_evidence_v2 import validate_packet,EvidenceRunner
from failure_evo.semantic_contract import SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
S={'schema':{'type':'object','additionalProperties':False,'required':['x','n'],'properties':{'x':{'type':['array','null'],'items':{'type':'number'}},'n':{'type':['integer','null']}}}}
def ev(kind,quotes=None,rule=None,src=None):return dict(kind=kind,quotes=quotes or [],scope='QUOTED_TEXT' if kind.startswith('EXPLICIT') else 'DERIVED_FIELDS' if kind=='DERIVED' else 'FULL_PROBLEM',rule=rule,from_field=src)
def packet():return dict(task_id='test',facts={'x':[1,2],'n':2},evidence={'x':ev('EXPLICIT_AFFIRMATION',['[1,2]']),'n':ev('DERIVED',rule='LIST_LENGTH',src='x')},review=dict(status='NO_ISSUE_OBSERVED',quotes=[],scope='FULL_PROBLEM'))
class Tests(unittest.TestCase):
 def setUp(self):self.p=packet();self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
 def test_empty_review_is_not_premise(self):self.assertEqual(validate_packet(S,'[1,2]',self.p),self.p['facts'])
 def test_not_stated_null(self):
  self.p['facts']={'x':None,'n':None};self.p['evidence']={k:ev('NOT_STATED') for k in ['x','n']};validate_packet(S,'not specified',self.p)
 def test_not_stated_cannot_assert(self):
  self.p['evidence']['n']=ev('NOT_STATED')
  with self.assertRaises(ValueError):validate_packet(S,'[1,2]',self.p)
 def test_explicit_needs_quote(self):
  self.p['evidence']['x']=ev('EXPLICIT_NEGATION')
  with self.assertRaises(ValueError):validate_packet(S,'[1,2]',self.p)
 def test_fake_quote(self):
  self.p['evidence']['x']['quotes']=['different']
  with self.assertRaises(ValueError):validate_packet(S,'[1,2]',self.p)
 def test_derived_wrong(self):
  self.p['facts']['n']=3
  with self.assertRaises(ValueError):validate_packet(S,'[1,2]',self.p)
 def test_arbitrary_derivation(self):
  self.p['evidence']['n']['rule']='MATHEMATICAL_GUESS'
  with self.assertRaises(ValueError):validate_packet(S,'[1,2]',self.p)
 def test_cycle(self):
  self.p['evidence']['x']=ev('DERIVED',rule='EXACT_COPY',src='n');self.p['evidence']['n']=ev('DERIVED',rule='EXACT_COPY',src='x')
  with self.assertRaises(ValueError):validate_packet(S,'[1,2]',self.p)
 def test_conflict_needs_quote(self):
  self.p['review']['status']='CONFLICT'
  with self.assertRaises(ValueError):validate_packet(S,'[1,2]',self.p)
 def test_null_cannot_compute(self):
  self.p['facts']['n']=None;self.p['evidence']['n']=ev('NOT_STATED')
  r=EvidenceRunner(SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),Path(self.tmp.name)/'worker'),S)
  o=r.run({'provenance':{'required_facts':['n']}},{'task_id':'test','problem':'[1,2]'},self.p,dict(origin='MODEL_PARSE',problem_sha256=fingerprint('[1,2]'),parsed_sha256=fingerprint(self.p),response_sha256='mock-bound'))
  self.assertEqual(o['stage'],'PREMISE_UNKNOWN');self.assertEqual(o['match']['status'],'UNKNOWN')
 def test_hidden_fields(self):
  with self.assertRaises(ValueError):guard('parser',{'semantics':S,'tasks':[{'task_id':'x','problem':'p','gold':'1'}]})
 def test_unauthorized(self):
  a=Adapter(Path(self.tmp.name)/'j',None,model='deepseek-flash')
  with self.assertRaises(PermissionError):a.preflight({'kind':'parser','public_input':{}})
 def test_native_schema_no_semantic_change(self):
  a=Adapter(Path(self.tmp.name)/'j',None,model='deepseek-flash',mock=True,sender=lambda body:None);a.kind='schema';v={'schema':S['schema'],'field_meanings':{'x':'data','n':'size'},'parser_instructions':'extract','prerequisites':'none'}
  raw={'model':'deepseek-flash','usage':{},'choices':[{'finish_reason':'stop','message':{'content':json.dumps(v)}}]}
  n=a._normalize_response(raw);w=json.loads(n['output'][0]['content'][0]['text']);self.assertEqual(json.loads(w['code']),v)
 def test_unrestricted_facts(self):
  self.p['facts']['x']=[2.5,1000000000000];self.p['evidence']['x']['quotes']=['2.5,1000000000000'];validate_packet(S,'2.5,1000000000000',self.p)
if __name__=='__main__':unittest.main()
