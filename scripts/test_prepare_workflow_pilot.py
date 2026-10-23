"""No API: causal-prefix isolation, shared-engineering exclusion and bounded pilot selection."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('pilot',Path(__file__).with_name('prepare_workflow_pilot.py'))
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)


class PilotTests(unittest.TestCase):
    def test_future_and_private_fields_do_not_enter_induction(self):
        task=dict(problem_id='source',prompt='public question',starter_code='',function_name='',hidden_tests='SECRET_HIDDEN')
        event=dict(stage='l1',request={'task':task},code='print(',public_feedback=dict(status='COMPILE_ERROR',visibility='public',public_cases=[],hidden_result='SECRET_HIDDEN'))
        workflow=dict(events=[event],selected={'code':'FUTURE_SENTINEL'},final_score='SECRET_HIDDEN')
        raw=dict(choices=[dict(message={'content':'print('},finish_reason='length')])
        first=p.checkpoint_input(workflow,0,raw)
        changed=copy.deepcopy(workflow);changed['events'].append(dict(stage='l2a',code='FUTURE_SENTINEL'));changed['selected']['code']='DIFFERENT_FUTURE'
        self.assertEqual(first,p.checkpoint_input(changed,0,raw))
        self.assertNotIn('SECRET_HIDDEN',p.canonical(first));self.assertNotIn('FUTURE_SENTINEL',p.canonical(first))
        self.assertEqual(len(first['candidate_ledger']),1)

    def test_existing_python_block_is_shared_infrastructure(self):
        text='```\nE = ?\n```\n```python\nprint(1)\n```'
        self.assertTrue(p.extraction_issue('E = ?',text))
        self.assertFalse(p.extraction_issue('print(', '```python\nprint('))
        self.assertFalse(p.extraction_issue('print(1)',text))

    def test_reuse_requires_later_different_task_and_code(self):
        def row(t,order,code,stage='l1'):
            return dict(family='delivery',status='ELIGIBLE_DEVELOPMENT',task_id=t,task_order=order,candidate_sha256=code,stage=stage)
        inventory=[row('b',2,'same'),row('a',1,'same'),row('a',1,'new','l2a'),row('c',3,'c'),row('c',3,'c2','l2a'),row('d',4,'d'),row('e',5,'e')]
        policy=dict(families=['delivery'],max_reuse_checkpoints_per_family=2)
        stream=p.select_streams(inventory,policy)[0]
        self.assertEqual(stream['discovery']['task_id'],'a')
        self.assertEqual([x['task_id'] for x in stream['reuse']],['c','d'])
        self.assertFalse(stream['independence_claim'])

    def test_no_opportunity_is_not_negative_effect(self):
        policy=dict(families=['delivery'],max_reuse_checkpoints_per_family=2)
        self.assertEqual(p.select_streams([],policy)[0]['status'],'NO_DISCOVERY')
        row=dict(family='delivery',status='ELIGIBLE_DEVELOPMENT',task_id='a',task_order=1,candidate_sha256='a',stage='l1')
        self.assertEqual(p.select_streams([row],policy)[0]['status'],'NO_LATER_REUSE_OPPORTUNITY')

    def test_preparation_never_authorizes_paid_dispatch(self):
        policy=p.read(p.ROOT/'experiments/workflow_pilot/policy.json')
        with self.assertRaisesRegex(RuntimeError,'PREPARATION_ONLY'):
            p.require_paid_ready(policy,{k:True for k in policy['paid_run_required']})
        self.assertEqual(policy['max_total_requests_proposed'],policy['max_generation_requests_proposed']+policy['max_source_validation_requests_proposed']+policy['max_reuse_requests_proposed'])

    def test_prepared_bundle_integrity_and_old_experiment_unchanged(self):
        report=p.read(p.OUT/'preparation.json')
        for f,h in report['historical_input_files'].items():self.assertEqual(p.sha(p.ROOT/f),h,f)
        for f,h in report['artifacts'].items():self.assertEqual(p.sha(p.OUT/f),h,f)
        old=p.read(p.SOURCE/'protocol.json')
        for f,h in old['frozen_files'].items():self.assertEqual(p.sha(f),h,f)
        self.assertEqual(report['new_model_calls'],0);self.assertEqual(report['new_permissions'],0)
        self.assertEqual(report['discovery_task_count'],1)

    def test_real_packets_never_include_later_candidate(self):
        streams=p.read(p.OUT/'checkpoint_streams.json')
        for stream in streams:
            row=stream['discovery'];packet=p.read(p.OUT/row['packet'])
            original=p.read(p.SOURCE/'branches'/row['task_id']/'FailureLearning/workflow.json')
            index=next(i for i,e in enumerate(original['events']) if e['stage']==row['stage'])
            prefix=[e['code'] for e in original['events'][:index+1] if 'code' in e]
            self.assertEqual([e['code'] for e in packet['candidate_ledger']],prefix)
            self.assertNotIn('selected',packet);self.assertNotIn('audit_cases',packet)
            self.assertEqual(packet['provenance']['role'],'historical_development_checkpoint')


if __name__=='__main__':unittest.main()
