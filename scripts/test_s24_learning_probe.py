import copy,json,tempfile,pathlib,unittest
from unittest.mock import patch
import s24_learning_probe as x
from s24_input_legality import validate
class Tests(unittest.TestCase):
 def setUp(self):self.rule=dict(hypothesis='uncertain',uncertainty='one source',rule=dict(min_comment_ratio=.2,min_code_chars=100,statuses=['WRONG_ANSWER'],action='STRIP_COMMENTS'))
 def test_permission_field_rejected(self):
  r=copy.deepcopy(self.rule);r['permission']='experimental'
  with self.assertRaises(ValueError):x.parse_rule(json.dumps(r))
 def test_wrong_predicate_type(self):
  r=copy.deepcopy(self.rule);r['rule']['min_comment_ratio']=True
  with self.assertRaises(ValueError):x.parse_rule(json.dumps(r))
 def test_target_choices_without_outcomes(self):
  p=x.e.read(x.RUN/'protocol.json');self.assertEqual([x.decide(self.rule,t['packet']) for t in p['targets']],['CP','P'])
 def test_illegal_input(self):
  self.assertFalse(validate('r0493','13 4\n0 3 8 18\n9 5')['valid'])
  self.assertFalse(validate('r2804','1\n1000000001')['valid'])
  self.assertFalse(validate('test-549','1 3 8 1 1 SAMPLE')['valid'])
 def test_full_mock_and_restart(self):
  p=x.e.read(x.RUN/'protocol.json');calls=[]
  with tempfile.TemporaryDirectory() as d:
   d=pathlib.Path(d);x.e.save(d/'protocol.json',p)
   def fake(w,t):
    body=json.loads(w);calls.append(body)
    text=json.dumps(self.rule) if len(calls)==1 else '```python\nprint(0)\n```'
    return dict(model='deepseek-flash',usage=dict(prompt_tokens=100,completion_tokens=100,total_tokens=200),choices=[dict(finish_reason='stop',message=dict(content=text))])
   judge=lambda *args:dict(passed=False,tests_run=1,tests_passed=0,status='WRONG_ANSWER')
   with patch.object(x,'RUN',d),patch.object(x.e,'real_sender',fake),patch.object(x.e,'worker',lambda *a:judge):
    x.run();self.assertEqual(len(calls),5);self.assertEqual(x.e.read(d/'state.json')['status'],'ONLINE_LOCKED')
    with self.assertRaises(RuntimeError):x.run()
    self.assertEqual(len(calls),5)
if __name__=='__main__':unittest.main()
