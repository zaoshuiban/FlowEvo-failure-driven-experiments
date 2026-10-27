import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.autonomous_openrouter import OpenRouterMechanismAdapter
from failure_evo.autonomous_mechanism import GeneratorConfig
from failure_evo.runtime import Budget
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.contracts import canonical
class Tests(unittest.TestCase):
 def test_final_wire_and_model_identity(self):
  with tempfile.TemporaryDirectory() as td:
   config=GeneratorConfig('gpt-5.4','gpt-5.4-20260305',2500000,15000000,'frozen fixture','2026-10-27')
   h=dict(decision='NO_MECHANISM',suggested_operator_kind='code_repair',source_evidence_ids=['e'],failure_pattern='fixture',root_cause_hypothesis='unknown',transferable_operation='none',expected_benefit='unknown',applicability_conditions=['unknown'],refusal_conditions=['unknown'],counterexamples=[],unresolved_uncertainties=['unknown'])
   wires=[]
   def send(w):
    wires.append(w);return dict(model='openai/gpt-5.4',id='MOCK',usage=dict(prompt_tokens=2,completion_tokens=3,total_tokens=5),choices=[dict(finish_reason='stop',message=dict(content=canonical(h)))])
   b=Budget(max_calls=3,max_tokens=200000);a=OpenRouterMechanismAdapter(Path(td)/'p',b,config=config,mock=True,sender=send)
   c=BoundedCompiler(a,b,Path(td)/'c',config.model,max_input_upper=32768)
   job=dict(stream_id='mock',family_id='f',job_id='j',evidence_ids=['e'],discovery={'evidence':[{'event_id':'e'}]})
   out=c.request(job,'induction',0,1)
   self.assertEqual(json.loads(out['specification']),h)
   self.assertFalse(wires[0]['provider']['allow_fallbacks']);self.assertEqual(wires[0]['response_format']['type'],'json_schema')
   self.assertEqual(out['usage']['total_tokens'],5)
   with self.assertRaises(ValueError):a._normalize_response(dict(model='other',usage={}))
 def test_wire_bound_default_and_explicit_extension(self):
  with tempfile.TemporaryDirectory() as td:
   config=GeneratorConfig('gpt-5.4','gpt-5.4-20260305',1,1,'fixture','today')
   j=dict(stream_id='s',family_id='f',phase='induction',slot=0,max_tokens=100,discovery={'evidence':[{'code':'x'*33000}]})
   a=OpenRouterMechanismAdapter(Path(td)/'p',Budget(),config=config,mock=True,sender=lambda _:None)
   with self.assertRaises(ValueError):a.preflight(j)
   b=OpenRouterMechanismAdapter(Path(td)/'q',Budget(),config=config,mock=True,sender=lambda _:None,max_wire_input_upper=65536)
   self.assertGreater(len(canonical(b.preflight(j)).encode())+256,32768)
   c=BoundedCompiler(b,Budget(),Path(td)/'c',config.model,max_input_upper=32768)
   from failure_evo.runtime import BudgetExhausted
   with self.assertRaises(BudgetExhausted):c.request(dict(j,job_id='j'),'induction',0,1)
   self.assertEqual(b.events.records(),[])
 def test_unknown_not_retried(self):
  with tempfile.TemporaryDirectory() as td:
   config=GeneratorConfig('gpt-5.4','gpt-5.4-20260305',1,1,'fixture','today');calls=[]
   def fail(w):calls.append(w);raise TimeoutError('fixture')
   a=OpenRouterMechanismAdapter(Path(td)/'p',Budget(max_calls=3,max_tokens=200000),config=config,mock=True,sender=fail)
   j=dict(stream_id='s',family_id='f',phase='induction',slot=0,max_tokens=100,discovery={'evidence':[{}]})
   with self.assertRaises(TimeoutError):a(j)
   with self.assertRaises(RuntimeError):a(j)
   self.assertEqual(len(calls),1)
if __name__=='__main__':unittest.main(verbosity=2)
