"""Exercise real Ed25519 verification without model calls or persistent keys."""
import base64
import subprocess
import tempfile
import unittest
from pathlib import Path

from failure_evo.math_gate_pool import review_signature_message, verify_review_signature


class SignedReviewTests(unittest.TestCase):
    def test_valid_signature_and_replay_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = root / 'test.pem'
            subprocess.run(['openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(secret)], check=True)
            public = subprocess.check_output(['openssl', 'pkey', '-in', str(secret), '-pubout'], text=True)
            plan = {'run': 'test', 'gate_reviewer_public_keys': {'reviewer': public}}
            review = {'reviewer': 'reviewer', 'Gate': [{'supported': True}]}
            message = root / 'message'
            message.write_bytes(review_signature_message(plan, 'F', 'A', review))
            sig = subprocess.check_output(
                ['openssl', 'pkeyutl', '-sign', '-inkey', str(secret), '-rawin', '-in', str(message)]
            )
            signature = base64.b64encode(sig).decode('ascii')
            verify_review_signature(plan, 'F', 'A', review, signature)
            scenarios = [
                (dict(plan, run='other'), 'F', 'A', review, signature),
                (plan, 'T', 'A', review, signature),
                (plan, 'F', 'B', review, signature),
                (plan, 'F', 'A', dict(review, Gate=[]), signature),
                (plan, 'F', 'A', review, None),
                (plan, 'F', 'A', review, base64.b64encode(b'0' * 64).decode('ascii')),
                (dict(plan, gate_reviewer_public_keys={}), 'F', 'A', review, signature),
            ]
            for index, args in enumerate(scenarios):
                with self.subTest(index=index), self.assertRaises(PermissionError):
                    verify_review_signature(*args)
