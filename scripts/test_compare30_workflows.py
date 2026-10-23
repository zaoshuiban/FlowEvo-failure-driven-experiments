"""Zero-API checks of the experiment seam, not generated solution fixtures."""
import asyncio, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('comparison',Path(__file__).with_name('compare30_workflows.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.setup()
class Checks(unittest.TestCase):
 def test_final_wire_preflight_before_reservation(self):
  with tempfile.TemporaryDirectory() as td:
   b=m.PersistentBudget(Path(td)/'b.jsonl',run_id='test',protocol_hash='frozen',**m.budget_config(1,0));t=m.Transport(b,m.RUN/'offline_mock')
   with patch.object(m.DeepSeekGenerator,'_post') as post:
    with self.assertRaises(m.BudgetExhausted):t.call([{'role':'user','content':'x'*33000}])
    post.assert_not_called();self.assertEqual(b.calls,0)
 def test_transport_persists_same_body_and_retains_unknown_money(self):
  with tempfile.TemporaryDirectory(dir=m.RUN) as td:
   p=Path(td);b=m.PersistentBudget(p/'b.jsonl',run_id='test',protocol_hash='frozen',**m.budget_config(1,0));t=m.Transport(b,p);raw={'model':'deepseek-flash','usage':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15},'choices':[{'message':{'content':'print(1)'},'finish_reason':'stop'}]}
   def post(body,key,timeout):
    self.assertEqual(body,m.read(p/'requests.json')[0]['request']);self.assertEqual(b.calls,1);return raw
   with patch.object(m.DeepSeekGenerator,'_post',side_effect=post),patch.object(m,'configured_api_key',return_value='MOCK'):
    out=t.call([{'role':'user','content':'solve'}]);self.assertEqual(out['text'],'print(1)')
   self.assertGreater(b.snapshot()['charged_or_reserved_cost_microusd'],0)
 def test_dataset_roles_and_permissions(self):
  m.verify();rows=m.read(m.RUN/'tasks.json');self.assertEqual(len(rows),30)
  for t in rows:
   self.assertFalse(set(c['input'] for c in t['public_cases']) & set(c['input'] for c in t['audit_cases']))
   self.assertFalse(set(t['task_public']) & {'input_output','reference_solution','audit_cases'})
  reg=m.RegistryUnion(m.FailureEvidenceStore(m.RUN/'test_evidence.jsonl'))
  self.assertEqual(reg.snapshot(stream_id='mock',task_index=1,experiment_id='mock',at=m.time.time()).cards,())
 def test_real_aflow_graph_mock_replay(self):
  class A(m.af.Adaptation):
   async def check_public(self,code):return 'no error'
  with tempfile.TemporaryDirectory() as td:
   t=m.af.ReplayTransport([{'response':'print(1)'}]*3+[{'solution_letter':'A'}]);a=A({},t,td)
   result=asyncio.run(a.run('read stdin, print answer',''))
   self.assertEqual(result['status'],'RETURNED_LOCKED');self.assertEqual(len(t.requests),4)
if __name__=='__main__':unittest.main()
