import unittest,tempfile,copy,json
from pathlib import Path
from run_algorithm_evidence import OUT,Adapter,guard,load,verify
class Test(unittest.TestCase):
 def setUp(self):self.v=load(OUT/'inputs.json')['0'];self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
 def r(self,arm):
  v=copy.deepcopy(self.v['base'])
  if arm!='T':v['failure_evidence']=copy.deepcopy(self.v['failures'])
  return dict(phase='candidate',slot=0,stage='analysis',arm=arm,public_input=v,max_tokens=8192)
 def test_arms(self):
  for arm in ['T','F','FC']:guard(self.r(arm))
 def test_no_gold(self):
  r=self.r('F');r['public_input']['source_tasks'][0]['gold_answer']='secret'
  with self.assertRaises(ValueError):guard(r)
 def test_correct_never_failure(self):
  r=self.r('F');r['public_input']['failure_evidence'][0]['correct']=True
  with self.assertRaises(ValueError):guard(r)
 def test_unverified_never_failure(self):
  r=self.r('F');r['public_input']['failure_evidence'][0]['correct']=None
  with self.assertRaises(ValueError):guard(r)
 def test_T_excludes_failure(self):
  r=self.r('T');r['public_input']['failure_evidence']=self.v['failures']
  with self.assertRaises(ValueError):guard(r)
 def test_F_FC_same_data(self):self.assertEqual(self.r('F')['public_input'],self.r('FC')['public_input'])
 def test_auth(self):
  a=Adapter(Path(self.tmp.name)/'j',None,model='deepseek-flash')
  with self.assertRaises(PermissionError):a.preflight(self.r('T'))
 def test_native_decline(self):
  a=Adapter(Path(self.tmp.name)/'j',None,model='deepseek-flash',mock=True,sender=lambda b:None);a.stage='analysis'
  v=dict(decision='NO_MECHANISM',observations=[],procedure_plan='',uncertainty='insufficient',invalid_operation=None,replacement_operation=None)
  raw=dict(model='deepseek-flash',usage={},choices=[dict(finish_reason='stop',message=dict(content=json.dumps(v)))])
  n=a._normalize_response(raw);w=json.loads(n['output'][0]['content'][0]['text']);self.assertEqual(json.loads(w['code']),v)
 def test_oracles(self):
  a=load(OUT/'private/oracle_audit.json');self.assertEqual(a['oracle_agreement_cases'],52)
 def test_frozen(self):self.assertEqual(verify()['max_requests'],36)
if __name__=='__main__':unittest.main()
