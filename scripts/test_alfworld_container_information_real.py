"""Zero API equivalence of authorized binding to the frozen B3 scheduler."""
import json,tempfile,unittest
from pathlib import Path
import run_alfworld_container_information_real as R
import run_alfworld_container_information as E
from test_alfworld_container_information import response,proposal,DECLINE,empty_eval
from failure_evo.run_health import RunUnhealthy

class BindingTests(unittest.TestCase):
    def test_frozen_wire_phases_versions_selection_and_resume(self):
        wires=[];executions=[]
        def sender(w):
            wires.append(w)
            phase=next(k for k,v in E.M.PROMPTS.items() if v==w['messages'][0]['content'])
            return response(proposal(('import os\n' if phase=='initial' else '')+DECLINE+('\n# behavior\n' if phase=='behavior' else '')),len(wires))
        def evaluate(row,p,b,out):
            executions.append(row['version']);return empty_eval(row,p,b,out)
        with tempfile.TemporaryDirectory(dir=E.ROOT/'runs') as d:
            frozen=E.run_mock(R.PRE,Path(d)/'frozen',sender=sender,evaluate=evaluate)
            expected=list(wires);expected_executions=list(executions);wires.clear();executions.clear()
            out=Path(d)/'binding';actual=R.run(out,mock_sender=sender,evaluate=evaluate)
            self.assertEqual(wires,expected);self.assertEqual(executions,expected_executions)
            self.assertEqual(actual['selection'],frozen['selection']);self.assertEqual(len(wires),36)
            before={str(x):E.P.sha(x) for x in out.rglob('*.jsonl')}
            self.assertEqual(R.run(out,mock_sender=lambda _:self.fail('resent'),evaluate=lambda *a:self.fail('rerun')),actual)
            self.assertEqual(before,{str(x):E.P.sha(x) for x in out.rglob('*.jsonl')})
            self.assertFalse(E.P.read(out/'authorization.json')['paid_api_authorized'])
            self.assertEqual(actual['paid_requests'],0)
    def test_unknown_blocks_new_requests(self):
        with tempfile.TemporaryDirectory(dir=E.ROOT/'runs') as d:
            calls=[]
            def sender(w):calls.append(w);raise TimeoutError('MOCK_UNKNOWN')
            with self.assertRaises(TimeoutError):R.run(Path(d)/'unknown',mock_sender=sender,evaluate=empty_eval)
            with self.assertRaises(RunUnhealthy):R.run(Path(d)/'unknown',mock_sender=sender,evaluate=empty_eval)
            self.assertEqual(len(calls),1)

if __name__=='__main__':unittest.main()
