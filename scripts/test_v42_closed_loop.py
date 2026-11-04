"""Explicit MOCK workflow, genuine Worker. Not a learning result."""
import tempfile,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
import run_v42_properties as run
from run_hard10_algorithm import save,load
class ClosedLoop(unittest.TestCase):
 def test_full_mock_revision_and_confirmation(self):
  with tempfile.TemporaryDirectory(prefix='engineering-v42-',dir=run.OUT) as td:
   out=Path(td);calls=[]
   schema=dict(type='object',additionalProperties=False,required=['expression'],properties={'expression':{'type':'string'}})
   save(out/'public_sources.json',{'expression':dict(problem='MOCK numeric literal',schema=schema,failure_evidence={'correct':False})})
   save(out/'private/development.json',{'expression':[{'expression':'2'}]})
   save(out/'private/confirmation.json',[dict(id='mock-unseen',family='expression',parameters={'expression':'7'},expected='7')])
   proposal=dict(diagnosis='MOCK off by one',replacement_hypothesis='MOCK remove offset',properties=[dict(id='mock-p',claim='MOCK literal evaluation',preconditions='MOCK integer literal',tests=[dict(relation='oracle_correct',left={'expression':'2'},right=None)])])
   def mock_call(fam,arm,stage,inp):
    calls.append(dict(arm=arm,stage=stage,origin='FIXED_MOCK'))
    if stage=='properties':return json.dumps(proposal)
    if stage=='review':return json.dumps(dict(diagnosis='MOCK',revision_plan='MOCK'))
    return 'def solve(parameters):\n return str(int(parameters["expression"])'+(' + 1' if arm=='B' else '')+')\n'
   with patch.object(run,'OUT',out),patch.object(run,'verify',return_value={}),patch.object(run,'model_call',side_effect=mock_call):
    run.run();run.confirm()
   arts=load(out/'candidate_freeze.json')['artifacts']['expression'];self.assertNotEqual(arts['B']['sha256'],arts['C']['sha256']);self.assertEqual(arts['C']['parent'],arts['B']['sha256'])
   initial=load(out/'properties/expression.json')['receipt']['records'][0]['verdict']['status'];self.assertEqual(initial,'ALGORITHM_COUNTEREXAMPLE')
   final=load(out/'post_revision_properties/expression-C.json')['records'][0]['verdict']['status'];self.assertEqual(final,'FINITE_SAMPLE_SUPPORTED')
   c=next(r for r in load(out/'confirmation_results.json') if r['arm']=='C');self.assertEqual(c['status'],'MATHEMATICAL_CORRECT')
   save(run.OUT/'mock_closed_loop_receipt.json',dict(origin='FIXED_MOCK_NOT_MODEL_LEARNING',model_api_calls=0,calls=calls,before=initial,after=final,confirmation=c['status'],parent_sha256=arts['B']['sha256'],child_sha256=arts['C']['sha256']))
if __name__=='__main__':unittest.main()
