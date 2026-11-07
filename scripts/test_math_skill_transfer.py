"""Targeted regressions for the skill-transfer data and outcome boundaries."""
import unittest
import tempfile
from pathlib import Path

from code_math.no_gold import PublicMathTask
from failure_evo.contracts import fingerprint
from failure_evo.math_skill_transfer import (
    SkillLifecycle, TransferTrain, checkpoint_messages, freeze_manifest, paired_outcome, retrieve_text,
)


class TransferBoundaryTests(unittest.TestCase):
    def test_masked_parameter_variant_cannot_cross_split(self):
        tasks = [
            PublicMathTask('source', 'Find the sum of the first 12 positive integers.'),
            PublicMathTask('dev', 'What is the smallest number of moves of a chess knight?'),
            PublicMathTask('test', 'Find the sum of the first 19 positive integers.'),
        ]
        rows = [
            dict(task_id=t.task_id, dataset='MOCK', dataset_revision='v1', source_row=i,
                 statement_hash=fingerprint(t.problem), split=split, source_run=None,
                 problem_family='UNKNOWN', exposure_status='NO_MATCH_IN_LOCAL_EXPOSURE_AUDIT',
                 scoring_reference_id=t.task_id, grading_method='mock')
            for i,(t,split) in enumerate(zip(tasks,('TRAIN','DEV','TEST')),1)
        ]
        with self.assertRaisesRegex(PermissionError, 'near template'):
            freeze_manifest(rows,tasks)

    def test_text_only_arm_cannot_accept_skill_evidence(self):
        task=PublicMathTask('heldout','A public test problem')
        lock=dict(task_id='heldout',final_output='The answer is 2')
        lock['locked_sha256']=fingerprint(lock)
        with self.assertRaisesRegex(PermissionError, 'isolation'):
            checkpoint_messages(task,lock,arm='C',skill_result={'scope':'OBJECTIVE_VALUE','result':'2'})
        with self.assertRaisesRegex(PermissionError, 'text cards only'):
            retrieve_text(task.problem,[{'code':'print(2)'}])

    def test_degradation_and_unknown_are_separate(self):
        self.assertEqual(paired_outcome({'correct':True},{'correct':False}),'NEGATIVE_TRANSFER')
        self.assertEqual(paired_outcome({'correct':True},{'correct':None}),'NOT_EVALUABLE')

    def test_evolution_isolated_and_frozen(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=SkillLifecycle('B',Path(tmp)/'B')
            d=SkillLifecycle('D',Path(tmp)/'D')
            base={'code_sha256':'v1'}
            variant={'code_sha256':'v2'}
            b.update('CREATE',base,evidence=['f'])
            d.update('CREATE',base,evidence=['f'])
            with self.assertRaises(PermissionError):
                b.update('REFINE',variant,parents=['v1'],evidence=['f'])
            with self.assertRaisesRegex(PermissionError,'DEV comparison'):
                d.update('SPECIALIZE',variant,parents=['v1'],evidence=['f'])
            d.update('RETIRE',base,parents=['v1'],evidence=['f'])
            self.assertEqual(len(b.events.records()),1)
            d.freeze([],None,'test-manifest')
            with self.assertRaisesRegex(PermissionError,'frozen'):
                d.update('CREATE',variant,evidence=['f'])

    def test_train_resume_keeps_settled_arms_and_stops_on_unhealthy_state(self):
        task = PublicMathTask('source', 'Public training statement')
        rows = [dict(task_id=task.task_id, split='TRAIN', statement_hash=fingerprint(task.problem))]
        manifest = dict(rows=rows, manifest_sha256=fingerprint(rows))
        failures = [dict(failure_id='f', problem=task.problem, correct=False,
                         final_output='Answer is 0', trajectory=[dict(text='Answer is 0',finish_reason='stop')])]
        calls = []

        def handle(job, fact, resuming):
            calls.append((job['arm'], resuming))
            if job['arm']=='B' and not resuming:
                raise RuntimeError('interrupt')
            return {'status':'FIXTURE'}

        def unhealthy():
            raise PermissionError('unknown send')

        with tempfile.TemporaryDirectory() as tmp:
            schedule = TransferTrain(tmp, manifest, failures, manifest_sha=fingerprint(rows),
                                     failures_sha=fingerprint(failures))
            handlers = dict.fromkeys('ABCD', handle)
            with self.assertRaisesRegex(RuntimeError, 'interrupt'):
                schedule.run(handlers, lambda: None)
            with self.assertRaisesRegex(PermissionError, 'unknown send'):
                schedule.run(handlers, unhealthy)
            result = schedule.run(handlers, lambda: None)
            self.assertEqual(calls, [('A',False),('B',False),('B',True),('C',False),('D',False)])
            self.assertEqual(len(result),4)
            with self.assertRaisesRegex(PermissionError, 'changed'):
                TransferTrain(tmp, manifest, failures, manifest_sha=fingerprint(rows), failures_sha='wrong')

    def test_transfer_budget_blocks_extra_arm_allocation_and_preserves_reopen(self):
        from failure_evo.math_transfer_launch import TransferBudget
        from failure_evo.runtime import BudgetExhausted

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            limits = TransferBudget(root,'engineering:test','test')
            first = limits.allocate(root/'C'/'budget.jsonl','TRAIN','C',10)
            second = limits.allocate(root/'C'/'budget.jsonl','TRAIN','C',10)
            self.assertEqual(first.config,second.config)
            with self.assertRaises(BudgetExhausted):
                limits.allocate(root/'extra'/'budget.jsonl','TRAIN','C',1)
            with self.assertRaises(PermissionError):
                limits.allocate(root/'C'/'budget.jsonl','TRAIN','B',10)

    def test_dev_reference_conflict_cannot_be_labeled_as_negative(self):
        from failure_evo.math_transfer_launch import build_dev_cases

        task = {'task_id':'d','problem':'Count eligible rows.'}
        row = dict(split='DEV',task_id='d',statement_hash=fingerprint(task['problem']),scoring_reference_id='ref')
        manifest = dict(rows=[row],manifest_sha256=fingerprint([row]))
        references = dict(manifest_sha256=manifest['manifest_sha256'],rows=[
            dict(task_id='d',problem_sha256=row['statement_hash'],reference_id='ref',
                 status='REFERENCE_CONFLICT',answer=None)])
        review = dict(manifest_sha256=manifest['manifest_sha256'],parent_version='p',candidate_version='c',
                      labels=[dict(task_id='d',supported=False,parameters=None,
                                   evidence_quotes=['eligible rows'],rationale='Different target')])
        with self.assertRaisesRegex(PermissionError,'unverified'):
            build_dev_cases(manifest,[task],references,review,{'code_sha256':'p'},{'code_sha256':'c'},
                            review_sha=fingerprint(review),references_sha=fingerprint(references))
