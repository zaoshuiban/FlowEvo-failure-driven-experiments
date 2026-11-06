"""Zero API regression for malformed candidate envelopes."""
import json
import unittest
from unittest.mock import Mock

from failure_evo.contracts import fingerprint
from failure_evo.math_cumulative_learning import (
    DELIVERY_EXAMPLE, request_candidate_delivery, settled_malformed_json,
)
from failure_evo.math_engineering_repair import receive_source


def response(content, *, finish='stop', meter=True):
    raw = dict(choices=[dict(finish_reason=finish, message={'content': content})],
               usage=dict(prompt_tokens=10, completion_tokens=5, total_tokens=15) if meter else {})
    return dict(raw_response=raw,response_sha256=fingerprint(raw),finish_reason=finish,
                transport_status='RESPONSE_RECEIVED',parse_status='COMPILE_OUTPUT_CONTRACT_ERROR',
                delivery_status='CONTRACT_INVALID')


class CandidateDeliveryTests(unittest.TestCase):
    def test_one_replacement_with_frozen_parent(self):
        malformed=response('{"code":"def solve(p):\\n    return 1')
        still_malformed=response('{"code":"incomplete')
        request=Mock(side_effect=[malformed,still_malformed])
        job={}
        result,replaced=request_candidate_delivery(request,job)
        self.assertTrue(replaced)
        self.assertEqual([c.args for c in request.call_args_list],[('candidate',0),('candidate',1)])
        self.assertEqual(job['delivery_repair']['parent_response_sha256'],malformed['response_sha256'])
        self.assertEqual(receive_source(result,'DEEPSEEK'),'DELIVERY_CONTRACT_INVALID')

    def test_unknown_truncation_and_semantic_rejection_have_no_replacement(self):
        for failure in (dict(transport_status='SEND_UNKNOWN'),
                        response('{"code":"incomplete',finish='length'),
                        response('{"code":"incomplete',meter=False),
                        response('{"code":"x","execution_authorized":true}')):
            with self.subTest(failure=failure):
                request=Mock(return_value=failure)
                self.assertEqual(request_candidate_delivery(request,{}),(failure,False))
                request.assert_called_once_with('candidate',0)

    def test_raw_payload_integrity_and_example_escaping(self):
        malformed=response('{"code":"incomplete')
        self.assertTrue(settled_malformed_json(malformed))
        malformed['raw_response']['choices'][0]['message']['content']+='modified'
        self.assertFalse(settled_malformed_json(malformed))
        sample=json.loads(DELIVERY_EXAMPLE)
        self.assertEqual(list(sample),['description','applicability','code'])
        self.assertIn("\n",sample['code'])
        self.assertIsInstance(json.loads(sample['description']),dict)
        self.assertIsInstance(json.loads(sample['applicability']),dict)
