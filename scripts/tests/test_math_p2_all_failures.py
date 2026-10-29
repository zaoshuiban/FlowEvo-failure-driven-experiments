import importlib.util,json,unittest,copy
from pathlib import Path
s=importlib.util.spec_from_file_location('fixtures',Path(__file__).with_name('test_math_no_gold.py'));old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
from failure_evo.math_p2_all_failures import *
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_operators import MathOperatorRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend

def response(v):return dict(model='openai/gpt-5.4',id='mock',choices=[dict(message=dict(content=json.dumps(v)),finish_reason='stop')],usage=dict(prompt_tokens=20,completion_tokens=20,total_tokens=40))
def real_rows():return json.loads((old.ROOT/'reports/math_p1_remaining82_20261027/confirmed_failures.json').read_text())
class AllTwelveTests(unittest.TestCase):
 setUp=old.MathTests.setUp
 tearDown=old.MathTests.tearDown
 def pipeline(self,values):
  rows=real_rows();b=old.budget(self.p/'budget',7);outputs=iter(values);self.wires=[]
  def send(w):self.wires.append(w);return response(next(outputs))
  a=AllFailuresGPTAdapter(self.p/'provider',b,model='gpt-5.4',mock=True,sender=send,max_wire_input_upper=65536)
  c=BoundedCompiler(a,b,self.p/'compiler','gpt-5.4',max_input_upper=65536,max_output_upper=8192)
  return AllFailuresEngineering(self.p/'engineering',c,MathOperatorRunner(FrozenLinuxBackend(image=old.IMAGE,worker_script=old.WORKER),budget=b)),dict(events=rows),a
 def test_real_twelve_projection_and_rejection(self):
  rows=real_rows();v=evidence_view(rows);self.assertEqual(len(v['events']),12)
  self.assertNotIn('gold_answer',canonical(v));self.assertNotIn('scorer',canonical(v));self.assertTrue(all(r['correct'] is False for r in v['events']))
  for r,p in zip(sorted(rows,key=lambda x:x['sequence']),v['events']):
   self.assertEqual(r['responses'][-1]['text'],p['attempts'][-1]['output']);self.assertFalse(p['attempts'][-1]['is_fragment'])
   self.assertIsNone(p['attempts'][0]['correctness'])
  for status in ('CONFIRMED_CORRECT','UNVERIFIED','TRUNCATED'):
   bad=copy.deepcopy(rows);bad[0]['final']['status']=status;bad[0]['evidence_id']=fingerprint({k:v for k,v in bad[0].items() if k!='evidence_id'})
   with self.assertRaises(PermissionError):evidence_view(bad)
 def test_no_mechanism(self):
  p,b,a=self.pipeline([dict(decision='NO_MECHANISM',summary='Mock only',mechanisms=[])])
  self.assertEqual(p.run(b)['candidates'],[]);self.assertEqual(len(self.wires),1)
  with self.assertRaises(RuntimeError):p.run(b)
 def test_mock_generated_exact_source_real_worker(self):
  rows=real_rows();m=dict(source_event_ids=[rows[0]['evidence_id']],**{k:'Engineering mock, not research evidence' for k in TEXT_FIELDS})
  code="def math_operator(context):\n    if context['problem'] == 'No mathematical question is supplied.':\n        return {'status': 'DECLINED', 'reason': 'no question'}\n    return {'status': 'APPLIED', 'answer': str(len(context['problem']))}\n"
  p,b,a=self.pipeline([dict(decision='PROPOSE',summary='mock',mechanisms=[m]),dict(code=code,description='Mock calculation',applicability='Engineering only')])
  r=p.run(b);self.assertTrue(r['candidates'][0]['engineering_passed']);self.assertEqual(r['candidates'][0]['applied_source_count'],1)
  generated=p.path/(r['candidates'][0]['code_sha256']+'.py');self.assertEqual(generated.read_text(),code)
  self.assertEqual(r['mathematical_correctness'],'NOT_EVALUATED');self.assertEqual(len(self.wires),2)
 def test_unauthorized_and_diagnostic_allowlist(self):
  b=old.budget(self.p/'b',7);a=AllFailuresGPTAdapter(self.p/'p',b,model='gpt-5.4',sender=lambda w:self.fail('sent'))
  with self.assertRaises(PermissionError):a.preflight({})
  p,b,a=self.pipeline([]);m=dict(source_event_ids=[b['events'][0]['evidence_id']],**{k:'mock' for k in TEXT_FIELDS})
  job=dict(phase='revision',slot=0,discovery=b,specification=canonical(dict(decision='PROPOSE',summary='mock',mechanisms=[m])),code='x',engineering_diagnostics=dict(static_errors=[],execution_statuses=[],correct=True),max_tokens=8192)
  with self.assertRaises(PermissionError):a.preflight(job)
 def test_unknown_not_resent(self):
  p,b,a=self.pipeline([]);calls=[]
  def fail(w):calls.append(w);raise OSError('mock unknown')
  a.sender=fail
  with self.assertRaises(OSError):p.run(b)
  with self.assertRaises(RuntimeError):p.run(b)
  self.assertEqual(len(calls),1)
 def test_engineering_revision_is_bounded_and_score_free(self):
  rows=real_rows();m=dict(source_event_ids=[rows[0]['evidence_id']],**{k:'Mock only' for k in TEXT_FIELDS})
  bad="import os\ndef math_operator(context):\n    return {'status': 'DECLINED', 'reason': 'mock'}\n"
  good="def math_operator(context):\n    return {'status': 'DECLINED', 'reason': 'unsupported'}\n"
  p,b,a=self.pipeline([dict(decision='PROPOSE',summary='mock',mechanisms=[m]),dict(code=bad,description='mock',applicability='mock'),dict(code=good,description='mock',applicability='mock')])
  r=p.run(b);self.assertEqual(len(r['candidates']),2);self.assertFalse(r['candidates'][0]['engineering_passed']);self.assertTrue(r['candidates'][1]['engineering_passed'])
  wire=json.loads(self.wires[-1]['messages'][1]['content']);self.assertEqual(set(wire['engineering_diagnostics']),{'static_errors','execution_statuses'})
  self.assertNotIn('answer',canonical(wire['engineering_diagnostics']));self.assertEqual(r['candidates'][1]['applied_source_count'],0)
if __name__=='__main__':unittest.main(verbosity=2)
