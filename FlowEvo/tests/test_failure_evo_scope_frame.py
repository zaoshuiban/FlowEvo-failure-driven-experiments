"""Frame evaluator regression: no model code executed or repair patch produced."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from experiment_capacity_scope_v2 import frame_review

class ScopeFrameTests(unittest.TestCase):
    spec=dict(tables=['fact','invfact'],length='n',boundary_alias='invf',function='main',bound=26)
    original='''def main():
    n = len(S)
    H = [0] * (n + 1)
    assert n + 1 == len(S) + 1
    fact = [1] * (n + 1)
    powers = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i
        powers[i] = powers[i - 1] * 26
    invfact = [1] * (n + 1)
    invfact[n] = fact[n]
    for i in range(n, 0, -1):
        invfact[i-1] = invfact[i] * i
    invf = invfact
    print(fact[n], H[n], powers[n])
'''
    # Trusted synthetic fixture only: not a generated artifact or capacity solution.
    def fixture(self):
        code=self.original.replace('    n = len(S)','    n = len(S)\n    capacity = max(n, 26)')
        code=code.replace('fact = [1] * (n + 1)','fact = [1] * (capacity + 1)')
        code=code.replace('    for i in range(1, n + 1):\n        fact[i] = fact[i - 1] * i\n        powers',
            '    for i in range(1, capacity + 1):\n        fact[i] = fact[i - 1] * i\n    for i in range(1, n + 1):\n        powers')
        return code.replace('invfact[n] = fact[n]','invfact[capacity] = fact[capacity]').replace('range(n, 0, -1)','range(capacity, 0, -1)')
    def check(self,code):return frame_review(self.original,code,self.spec)['passed']
    def test_narrow_split_keeps_non_target_loop(self):self.assertTrue(self.check(self.fixture()))
    def test_global_expression_rejected(self):self.assertFalse(self.check(self.fixture().replace('n + 1','capacity + 1')))
    def test_unrelated_array_rejected(self):self.assertFalse(self.check(self.fixture().replace('H = [0] * (n + 1)','H = [0] * (capacity + 1)')))
    def test_unrelated_loop_rejected(self):self.assertFalse(self.check(self.fixture().replace('range(1, n + 1)','range(1, capacity + 1)')))
    def test_consumer_subscript_rejected(self):self.assertFalse(self.check(self.fixture().replace('print(fact[n]','print(fact[capacity]')))
    def test_length_change_rejected(self):self.assertFalse(self.check(self.fixture().replace('n = len(S)','n = 26')))
    def test_extra_side_effect_rejected(self):self.assertFalse(self.check(self.fixture().replace('    invf = invfact','    print(7)\n    invf = invfact')))
    def test_missing_boundary_rejected(self):self.assertFalse(self.check(self.fixture().replace('invf = invfact','alias = invfact')))

class CompactScopeTests(unittest.TestCase):
    def test_actual_failed_revision_preserves_current_source_and_diagnostics(self):
        import copy,json
        from resume_capacity_scope_v2 import CompactScopeGenerator
        from failure_evo.contracts import canonical
        path=ROOT/'runs/s12j_capacity_scope_v2_20261022_01/candidate_1/revision_input.json'
        if not path.exists():self.skipTest('real revision fixture absent')
        request=json.loads(path.read_text());request.update(phase='revision',slot=0,max_tokens=4096)
        before=copy.deepcopy(request)
        wire=CompactScopeGenerator.prepare(request)
        self.assertEqual(request,before)
        self.assertLess(len(canonical(wire).encode()),65536)
        # Provider embeds the projected request in the user JSON message.
        payload=json.loads(wire['messages'][-1]['content'])
        self.assertEqual(payload['revision_parent'],request['revision_parent'])
        self.assertEqual(payload['candidate_code'],request['candidate_code'])
        self.assertEqual(payload['static_diagnostics'],request['static_diagnostics'])
        self.assertEqual(payload['functional_diagnostics']['source_reason'],'mixed_initializer')
        self.assertNotIn('code',payload['version_parent'])
        for old,new in zip(request['functional_diagnostics']['failure_diagnostics'],payload['functional_diagnostics']['failure_diagnostics']):
            self.assertEqual(old['reason'],new['reason'])
            self.assertEqual(old['id'],new['id'])
            self.assertIn('diagnostic_program_sha256',new)

if __name__=='__main__':unittest.main()
