import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import FrozenInstanceError
from failure_evo.autonomous_generation import DeepSeekCompilerAdapter
from failure_evo.delivery_observation import DeliveryObservation
from failure_evo.runtime import Budget

class DeliveryTests(unittest.TestCase):
    def receive(self, content, finish='stop'):
        raw = dict(id='fixture', model='deepseek-flash', choices=[dict(finish_reason=finish,
            message=dict(content=content))], usage=dict(prompt_tokens=10,completion_tokens=20,total_tokens=30))
        with tempfile.TemporaryDirectory() as p:
            adapter=DeepSeekCompilerAdapter(Path(p)/'events',Budget(),model='deepseek-flash',mock=True,sender=lambda _:raw)
            adapter.preflight=lambda _: {'model':'mock'}
            result=adapter(dict(stream_id='s',family_id='f',phase='candidate',slot=0))
        self.assertEqual(result['raw_response'],raw)
        self.assertEqual(result['usage']['total_tokens'],30)
        self.assertEqual(result['provider_finish_reason'],finish)
        self.assertEqual(result['finish_reason'],finish)
        self.assertEqual(result['program_status'],'NOT_CHECKED')
        self.assertEqual(result['mathematics_status'],'NOT_EVALUATED')
        self.assertEqual(result['candidate_status'],'NOT_REGISTERED')
        return result

    def test_missing_metadata_is_not_transport_or_algorithm_failure(self):
        r=self.receive(json.dumps({'code':'description="x"\napplicability="y"\ndef solve(x): return x'}))
        self.assertEqual(r['contract_status'],'REJECTED')
        self.assertEqual(r['contract_error'],'MISSING_REQUIRED_FIELDS: applicability,description')
        self.assertNotIn('code',r)
        self.assertEqual(r['delivery_status'],'CONTRACT_INVALID')

    def test_invalid_json(self):
        self.assertEqual(self.receive('{')['contract_status'],'REJECTED')

    def test_truncated(self):
        self.assertEqual(self.receive('{}','length')['delivery_status'],'MODEL_INCOMPLETE')

    def test_valid_contract_does_not_assert_python_correct(self):
        r=self.receive(json.dumps(dict(code='not python !',description='d',applicability='a')))
        self.assertEqual(r['contract_status'],'ACCEPTED')

    def test_host_transition(self):
        state=DeliveryObservation.received({'choices':[{'finish_reason':'stop'}]})
        with self.assertRaises(FrozenInstanceError):state.provider_finish_reason='error'
        with self.assertRaises(ValueError):state.decide_contract(False,'bad').decide_contract(True)

if __name__=='__main__':unittest.main()
