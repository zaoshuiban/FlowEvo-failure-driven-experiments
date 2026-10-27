"""No network; provider parity and final wire ceilings."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.autonomous_deepseek_v2 import DeepSeekMechanismAdapter,DeepSeekMechanismConfig
from failure_evo.autonomous_mechanism import MechanismCompilerAdapter,GeneratorConfig
from failure_evo.contracts import canonical
from failure_evo.runtime import Budget
from failure_evo.compile_queue import BoundedCompiler
CFG=DeepSeekMechanismConfig('deepseek-flash','DeepSeek-V4.1-Flash-1017',300000,1200000,'frozen quote','2026-10-27')
H=dict(decision='NO_MECHANISM',suggested_operator_kind='code_repair',source_evidence_ids=['e'],failure_pattern='fixture',root_cause_hypothesis='unknown',transferable_operation='none',expected_benefit='unknown',applicability_conditions=['unknown'],refusal_conditions=['unknown'],counterexamples=[],unresolved_uncertainties=['unknown'])
class Tests(unittest.TestCase):
 def test_same_evidence_prompt_and_contract(self):
  with tempfile.TemporaryDirectory() as td:
   b=Budget(max_calls=3,max_tokens=200000);seen=[]
   raw=dict(model='deepseek-flash',id='MOCK',choices=[dict(finish_reason='stop',message=dict(content=canonical(H)))],usage=dict(prompt_tokens=5,completion_tokens=6,total_tokens=11))
   def send(w):seen.append(w);return raw
   a=DeepSeekMechanismAdapter(Path(td)/'p',b,config=CFG,mock=True,sender=send,max_wire_input_upper=65536)
   j=dict(job_id='j',family_id='f',stream_id='s',evidence_ids=['e'],discovery={'evidence':[{'event_id':'e'}]})
   c=BoundedCompiler(a,b,Path(td)/'c',a.model,max_input_upper=65536,max_output_upper=8192)
   result=c.request(j,'induction',0,1,output_upper=8192)
   self.assertEqual(json.loads(result['specification']),H);self.assertEqual(result['raw_response'],raw);self.assertEqual(result['origin'],'MOCK')
   g=MechanismCompilerAdapter(Path(td)/'g',Budget(),config=GeneratorConfig('gpt-fixture','MOCK',1,1,'fixture','today'),mock=True,sender=lambda _:None,max_wire_input_upper=65536)
   other=g.preflight(dict(j,phase='induction',slot=0,max_tokens=8192))
   self.assertEqual(seen[0]['messages'][1],other['input'][1]);self.assertTrue(seen[0]['messages'][0]['content'].startswith(other['input'][0]['content']))
   self.assertEqual(seen[0]['response_format'],{'type':'json_object'})
   self.assertEqual(result['generator_config']['model'],'deepseek-flash')
 def test_upper_bound_and_authorization(self):
  with tempfile.TemporaryDirectory() as td:
   a=DeepSeekMechanismAdapter(Path(td)/'p',Budget(),config=CFG,mock=True,sender=lambda _:None)
   j=dict(phase='induction',max_tokens=8192,discovery={'evidence':[{'code':'x'*33000}]})
   with self.assertRaises(ValueError):a.preflight(j)
   a=DeepSeekMechanismAdapter(Path(td)/'q',Budget(),config=CFG,mock=True,sender=lambda _:None,max_wire_input_upper=65536)
   self.assertGreater(len(canonical(a.preflight(j))),32768)
   a=DeepSeekMechanismAdapter(Path(td)/'r',Budget(),config=CFG)
   with self.assertRaises(PermissionError):a.preflight(j)
 def test_truncation_and_unknown(self):
  with tempfile.TemporaryDirectory() as td:
   sent=[]
   def fail(w):sent.append(w);raise TimeoutError('fixture')
   a=DeepSeekMechanismAdapter(Path(td)/'p',Budget(),config=CFG,mock=True,sender=fail)
   self.assertEqual(a._normalize_response({'choices':[{'finish_reason':'length'}]})['status'],'incomplete')
   j=dict(stream_id='s',family_id='f',slot=0,phase='induction',max_tokens=100,discovery={'evidence':[{}]})
   with self.assertRaises(TimeoutError):a(j)
   with self.assertRaises(RuntimeError):a(j)
   self.assertEqual(len(sent),1)
if __name__=='__main__':unittest.main(verbosity=2)
