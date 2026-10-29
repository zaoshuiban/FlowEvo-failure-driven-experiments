import sys,unittest,copy,json
from run_math_v33 import OUT,load,guard,Adapter,sha,ROOT
from failure_evo.structured_semantics import check_parse,StructuredRunner
from failure_evo.semantic_contract import SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from run_math_v33 import WORKER,IMAGE
class Tests(unittest.TestCase):
 def setUp(self):
  self.s=load(OUT/'semantics.json');self.f=load(OUT/'trusted_semantics/development.json')[0]['facts'];self.p={'task_id':'mock','facts':self.f,'evidence':{k:['text'] for k in self.f}}
 def test_good(self):self.assertEqual(check_parse(self.s,'text',self.p),self.f)
 def test_quote(self):
  self.p['evidence']['operands']=['invented']
  with self.assertRaises(ValueError):check_parse(self.s,'text',self.p)
 def test_missing_quote(self):
  self.p['evidence']['operands']=[]
  with self.assertRaises(ValueError):check_parse(self.s,'text',self.p)
 def test_extra_gold(self):
  for k in ['gold_answer','reference_answer','trusted_semantics']:
   with self.assertRaises(ValueError):guard('schema',dict(load(OUT/'base.json'),**{k:'secret'}))
 def test_public_only(self):
  with self.assertRaises(ValueError):guard('parser',{'semantics':self.s,'tasks':[{'task_id':'t','problem':'p','answer':1}]})
 def test_authorization(self):
  a=Adapter(OUT/'mock_unauthorized.jsonl',None,model='deepseek-flash')
  with self.assertRaises(PermissionError):a.preflight(dict(kind='parser',public_input={}))
 def test_solver_mutation(self):
  b=load(OUT/'base.json');b['solver_code']+='\n'
  with self.assertRaises(ValueError):guard('schema',b)
 def test_trusted_not_runtime(self):
  split=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),OUT/'mock_worker.jsonl');r=StructuredRunner(split,self.s)
  with self.assertRaises(PermissionError):r.run({},dict(task_id='mock',problem='text'),self.p,dict(origin='TRUSTED_REVIEW'))
  with self.assertRaises(PermissionError):r.diagnose_trusted({},self.f)
 def test_schema_hash_bound(self):
  split=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),OUT/'mock_worker.jsonl');r=StructuredRunner(split,self.s)
  a=copy.deepcopy(load(OUT/'FS/artifact.json'));a['provenance']['semantics_sha256']='wrong'
  with self.assertRaises(PermissionError):r.diagnose_trusted(a,self.f,offline_attribution=True)
 def test_actual_frozen_source_bound(self):
  a=load(OUT/'FS/artifact.json');self.assertEqual(sha(a['solver_path']),load(OUT/'base.json')['solver_sha256']);self.assertEqual(sha(a['matcher_path']),a['matcher_sha256'])
if __name__=='__main__':unittest.main()
