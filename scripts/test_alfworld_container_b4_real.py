"""Zero API equivalence of the B4 real binding to its frozen scheduler."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from collections import Counter
import run_alfworld_container_b4_real as R
import run_alfworld_container_b4 as F
from test_alfworld_container_b4 import evaluate,response,proposal,DECLINE
from failure_evo.run_health import RunUnhealthy

class BindingTests(unittest.TestCase):
    def test_full_54_wire_execution_selection_and_settled_resume(self):
        wires=[];executions=[]
        def sender(w):
            wires.append(w);phase=next(k for k,v in R.M.PROMPTS.items() if v==w['messages'][0]['content'])
            return response(proposal(('import os\n' if phase=='initial' else '')+DECLINE+('\n# behavior\n' if phase=='behavior' else '')),len(wires))
        def ev(row,p,cases,role,b,out):
            executions.append((role,row['version'],[c['id'] for c in cases]));return evaluate(row,p,cases,role,b,out)
        with tempfile.TemporaryDirectory(dir=R.D.ROOT/'runs') as d:
            original=F.run_mock(R.PRE,Path(d)/'frozen',sender=sender,evaluate=ev)
            expected_wires=list(wires);expected_ex=list(executions);wires.clear();executions.clear()
            out=Path(d)/'real';actual=R.run(out,sender=sender,evaluate=ev)
            self.assertEqual(wires,expected_wires);self.assertEqual(executions,expected_ex);self.assertEqual(actual['selection'],original['selection']);self.assertEqual(len(wires),54)
            hashes={str(f):R.P.sha(f) for f in out.rglob('*.jsonl')}
            again=R.run(out,sender=lambda _:self.fail('resent'),evaluate=lambda *a:self.fail('rerun'))
            self.assertEqual(actual,again);self.assertEqual(hashes,{str(f):R.P.sha(f) for f in out.rglob('*.jsonl')})
            self.assertFalse(R.P.read(out/'authorization.json')['paid_api_authorized'])
    def test_unknown_is_global_and_no_resend(self):
        calls=[]
        def sender(w):calls.append(w);raise TimeoutError('MOCK_UNKNOWN')
        with tempfile.TemporaryDirectory(dir=R.D.ROOT/'runs') as d:
            out=Path(d)/'unknown'
            with self.assertRaises(TimeoutError):R.run(out,sender=sender,evaluate=evaluate)
            with self.assertRaises(RunUnhealthy):R.run(out,sender=sender,evaluate=evaluate)
            self.assertEqual(len(calls),1)
    def test_twelve_abstain_stop(self):
        calls=[]
        def sender(w):calls.append(w);return response(dict(decision='ABSTAIN',reason='MOCK_ONLY'),len(calls))
        with tempfile.TemporaryDirectory(dir=R.D.ROOT/'runs') as d:
            result=R.run(Path(d)/'stop',sender=sender,evaluate=lambda *a:self.fail('evaluation'))
            self.assertEqual(len(calls),12);self.assertEqual(result['status'],'MOCK_EARLY_STOP_ALL_ABSTAIN')
    def test_paid_path_requires_exact_authorization_before_transport(self):
        from alfworld_.recovery_acquisition import RecoveryAdapter
        from failure_evo.wire_input_policy import check_wire
        with tempfile.TemporaryDirectory(dir=R.D.ROOT/'runs') as d:
            out=Path(d)/'auth';p=R.freeze(out);b=R.account(out/'S11',p,'S11');cfg=b.config
            a=RecoveryAdapter(out/'unused.jsonl',b,model=p['model'],mock=False,stage='analyze',payload={},parser=lambda x:x,
                protocol=R.M.VERSION,analysis_prompt=R.M.PROMPTS['initial'],temperature=p['temperature'],
                max_wire_input_upper=p['input_policy']['max_input_tokens'],wire_input_policy=p['input_policy'])
            with self.assertRaises(PermissionError):a._authorize()
            a.authorization=dict(run_id=cfg['run_id'],protocol_hash=cfg['protocol_hash'],model=p['model'],protocol=R.M.VERSION,max_cost_microusd=cfg['max_cost_microusd'],paid_api_authorized=True)
            a._authorize();a.authorization['max_cost_microusd']+=1
            with self.assertRaises(PermissionError):a._authorize()
            self.assertEqual(sum(R.account(out/c,p,c).config['max_cost_microusd'] for c in R.M.CELLS),36000000)
            self.assertEqual(sum(R.account(out/c,p,c).config['max_calls'] for c in R.M.CELLS),54)

if __name__=='__main__':unittest.main()
