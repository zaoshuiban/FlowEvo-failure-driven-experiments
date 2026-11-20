"""Explicit domain boundaries; not all domains are executable acquisition-ready."""
import ast
from core.utils import visible_public_tests, infer_task_entry_point
from eval.verifier import verify_function_task

class CodeAdapter:
    status = 'READY_MBPP_HUMANEVAL_PUBLIC_ASSERTS'
    def enhanced_training_projection(self, task, source, qualified_record):
        """Project only an audited binary training verdict and evidence binding.

        Private evaluator objects are never accepted as execution feedback or
        copied wholesale. This payload is not a compiler success trace.
        """
        from failure_evo.acquisition_selectors import eligible_failure
        from failure_evo.skill_runtime import sha
        if not eligible_failure(qualified_record):raise ValueError('UNQUALIFIED_TRAINING_EVIDENCE')
        if qualified_record.get('problem_id')!=task.task_id or sha(source)!=qualified_record.get('final_source_sha256'):
            raise ValueError('ENHANCED_EVIDENCE_BINDING_MISMATCH')
        return dict(task=self.public_view(task),actor_source=source,
            independent_training_feedback='FAIL',evidence_id=qualified_record['evidence_id'],
            source_sha256=qualified_record['final_source_sha256'],
            dependency_bundle_sha256=qualified_record['dependency_bundle_sha256'],
            scoring_suite_sha256=qualified_record['scoring_suite_sha256'])

    def public_view(self, task):
        if task.benchmark not in {'mbpp', 'humaneval', 'taco'}:raise ValueError('ADAPTER_NOT_READY')
        if task.benchmark == 'taco' and not task.metadata.get('taco_function_subset'):raise ValueError('ADAPTER_NOT_READY')
        if task.metadata.get('data_role') not in {'train', 'development'}:raise ValueError('EVALUATION_DATA_FORBIDDEN')
        if not task.metadata.get('training_validation_public'):raise ValueError('PUBLIC_VALIDATION_NOT_DECLARED')
        tests = visible_public_tests(task)
        if task.benchmark in {'humaneval','taco'}:tests = task.metadata.get('public_training_tests', [])
        if not tests or any(not ast.parse(t).body or not all(isinstance(n, ast.Assert) for n in ast.parse(t).body) for t in tests):
            raise ValueError('EMPTY_OR_NONASSERT_VALIDATION')
        value = dict(problem_id=task.task_id, domain='code', benchmark=task.benchmark,
                    prompt=task.prompt, entry_point=infer_task_entry_point(task), public_tests=list(tests))
        if task.benchmark == 'taco':value['call_protocol'] = task.metadata['call_protocol']
        return value

    def verify(self, task, code, sandbox, public):
        # Setup/private metadata are not copied into the public verification task.
        clean = task.model_copy(deep=True)
        clean.test_setup_code = ''
        fb = verify_function_task(clean, code, sandbox, tests=public['public_tests'], scope='visible_public')
        fb.metrics['acquisition_public_tests'] = public['public_tests']
        fb.metrics['feedback_visibility'] = 'public'
        if not fb.metrics.get('total_test_count') or not fb.executed_code:
            raise ValueError('NO_EXECUTED_VALIDATION')
        return fb

class MathAdapter:
    status = 'ADAPTER_NOT_READY'
    missing = ['teacher success adjudication respecting no_gold', 'native solver operation selection/resumption']
    def public_view(self, task):
        from code_math.no_gold import PublicMathTask
        if not isinstance(task, PublicMathTask):raise TypeError('PUBLIC_MATH_TASK_REQUIRED')
        return task.to_dict()
    def verify(self, *args, **kwargs):raise RuntimeError('ADAPTER_NOT_READY')

class InteractionAdapter:
    status = 'ADAPTER_NOT_READY'
    missing = ['agent-selected parameterized Python operation', 'teacher prefix/suffix accounting integration']
    def public_view(self, goal, observation, admissible_commands, history):
        return dict(goal=goal, observation=observation, admissible_commands=list(admissible_commands), history=history)
    def verify(self, *args, **kwargs):raise RuntimeError('ADAPTER_NOT_READY')
