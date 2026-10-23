"""Static-only regression tests; generated artifacts are parsed, never executed."""
import hashlib
import json
from pathlib import Path
import sys
import textwrap
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from failure_evo.model_api import validate_compile_output
from failure_evo.contracts import PublicFeedback


def review(body):
    code='def repair_operator(context):\n'+textwrap.indent(textwrap.dedent(body).strip(),'    ')+'\n'
    return validate_compile_output(dict(code=code,description='engineering fixture',applicability='fixture only'))

class StaticContractTests(unittest.TestCase):
    def test_try_except_returns(self):
        r=review('''
        try:
            return {'status':'declined'}
        except Exception:
            return {'status':'error'}
        ''')
        self.assertTrue(r['static_pass'])
    def test_handler_fallthrough_rejected(self):
        r=review('''
        try:
            return {'status':'declined'}
        except Exception:
            pass
        ''')
        self.assertFalse(r['return_protocol_static_pass'])
    def test_try_else_return(self):
        r=review('''
        try:
            value = context.get('x')
        except Exception:
            return {'status':'error'}
        else:
            return {'status':'declined'}
        ''')
        self.assertTrue(r['static_pass'])
    def test_try_normal_fallthrough_rejected(self):
        r=review('''
        try:
            value = 1
        except Exception:
            return {'status':'error'}
        ''')
        self.assertFalse(r['return_protocol_static_pass'])
    def test_finally_return_covers_fallthrough(self):
        self.assertTrue(review('''
        try:
            value = context.get('x')
        finally:
            return {'status':'declined'}
        ''')['static_pass'])
    def test_finally_bad_return_rejected(self):
        self.assertFalse(review('''
        try:
            return {'status':'declined'}
        finally:
            return None
        ''')['static_pass'])
    def test_finally_pass_preserves_missing_return(self):
        self.assertFalse(review('''
        try:
            if context:
                return {'status':'declined'}
        finally:
            pass
        ''')['return_protocol_static_pass'])
    def test_nested_try_followed_by_fallback(self):
        self.assertTrue(review('''
        try:
            try:
                if context:
                    return {'status':'declined'}
            except ValueError:
                return {'status':'error'}
        except Exception:
            pass
        return {'status':'declined'}
        ''')['static_pass'])
    def test_loop_does_not_imply_return(self):
        self.assertFalse(review('''
        for row in context:
            return {'status':'declined'}
        ''')['return_protocol_static_pass'])
        self.assertFalse(review('''
        for row in context:
            break
        else:
            return {'status':'declined'}
        ''')['return_protocol_static_pass'])
    def test_raise_is_not_success_proof(self):
        r=review('''
        if context:
            raise ValueError('bad context')
        return {'status':'declined'}
        ''')
        self.assertTrue(r['static_pass']);self.assertIn('EXCEPTION_PATH_REQUIRES_HOST_HANDLING',r['warnings'])
        self.assertEqual(r['execution'],'NOT_RUN')
    def test_context_case_status_error_with_aliases(self):
        r=review('''
        rows = context.get('candidate_ledger', [])
        for row in rows:
            feedback = row.get('public_feedback', {})
            cases = feedback.get('public_cases', [])
            for case in cases:
                alias = case
                if alias.get('status') == 'PASS':
                    return {'status':'applied','selected_candidate_id':row['candidate_id']}
        return {'status':'declined'}
        ''')
        self.assertTrue(r['return_protocol_static_pass'])
        self.assertEqual(r['errors'],['COMPILE_CONTEXT_CONTRACT_ERROR'])
        self.assertTrue(r['context_contract_findings'][0]['line']>0)
    def test_valid_case_fields_and_aggregate_status(self):
        r=review('''
        feedback = context['public_feedback']
        for case in feedback['public_cases']:
            actual = case.get('actual')
            expected = case.get('expected')
        if feedback.get('status') == 'PUBLIC_PASS':
            return {'status':'declined'}
        return {'status':'declined'}
        ''')
        self.assertTrue(r['static_pass'])
        fb=PublicFeedback.project(dict(visibility='public',status='PUBLIC_PASS',cases=[dict(visibility='public',legal_verified=True,input='1',expected='1',actual='1',status='PASS')])).to_dict()
        self.assertNotIn('status',fb['public_cases'][0])
    def test_unrelated_status_not_flagged(self):
        self.assertTrue(review('''
        case = {'status':'PASS'}
        if case.get('status'):
            return {'status':'declined'}
        return {'status':'declined'}
        ''')['static_pass'])
    def test_real_b2_source_reinspection_unchanged(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'runs/s12b2_20261021_01'
        response=json.loads((run/'candidate_1.response.json').read_text())
        code=(run/'candidate_1.py').read_bytes()
        self.assertEqual(hashlib.sha256(code).hexdigest(),'aad47518e67e90e8f1337a182296ab9452a87d5ebd4e812e8e0c484eda56cf41')
        r=validate_compile_output({k:response[k] for k in ('code','description','applicability')})
        self.assertTrue(r['return_protocol_static_pass'])
        self.assertEqual(r['errors'],['COMPILE_CONTEXT_CONTRACT_ERROR'])
        self.assertFalse(r['static_pass']);self.assertEqual(r['execution'],'NOT_RUN')

if __name__=='__main__':unittest.main()
