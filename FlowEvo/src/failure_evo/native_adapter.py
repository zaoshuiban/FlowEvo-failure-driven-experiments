"""Public-feedback seam for the archived benchmark.py/CodeSkillLibrary path.

The host supplies the actual model, extractor, task-instance factory, public
checker and a separate native success library per arm. Importing this module
neither creates an API client nor imports the archived benchmark's key access.
"""
import copy
import hashlib
from pathlib import Path

from .contracts import PublicTaskView
from .failure_events import checked_public_feedback
from .runtime import Controller

SYSTEM_PROMPT = 'You are an expert competitive programmer. Produce a correct and efficient Python solution.'


def prompt_for(task):
    # Preserve the archived benchmark's base prompt exactly, including spacing.
    parts = ['Solve this competitive programming problem in Python 3.10. Return the complete solution in one ```python``` block.', 'Problem:\n' + task['prompt']]
    if task['starter_code']:
        parts += ['Starter code / required signature:\n' + task['starter_code']]
    if task['function_name']:
        parts += ['Use the required function/method named ' + task['function_name'] + '. Preserve the required class and signature; do not read stdin.']
    else:
        parts += ['Write a complete program that reads standard input and prints the required output.']
    parts += ['Think carefully about correctness, edge cases and time/memory complexity.']
    return '\n\n'.join(parts)


class NativeBenchmarkSession:
    """One independent successful-solution library and optional failure plugin.

    This explicitly revises the archived all-tests feedback protocol: only
    audited public results may stop attempts or update CodeSkillLibrary.
    Shared engineering baseline is identical with the failure plugin on/off.
    """
    def __init__(self, model_call, public_evaluator, context, *, library,
                 instance_factory, extract_code, plugin=None, clock=None, max_output=32768):
        self.model_call, self.public_evaluator, self.context = model_call, public_evaluator, context
        self.library, self.instance_factory, self.extract_code = library, instance_factory, extract_code
        self.plugin, self.clock, self.max_output = plugin, clock, max_output
        self.running = False

    def solve(self, raw_task, budget):
        if self.running:
            raise RuntimeError('native library session must execute sequentially')
        self.running = True
        try:
            public = PublicTaskView.project(raw_task)
            instance = self.instance_factory(public.to_dict())
            library_context = self.library.retrieve(instance).get('context', '')
            def request_adapter(payload):
                payload = copy.deepcopy(payload)
                prompt = prompt_for(payload['task'])
                if payload['stage'] in ('l3', 'l4'):
                    prompt += '\n\nPrevious candidate:\n```python\n' + payload['previous_candidate'] + '\n```\n\nVerifier feedback: ' + payload['feedback']['summary'] + '\nFix the solution and return the corrected complete Python program/function.'
                    if library_context:
                        prompt += '\n\nReference from a previously solved problem:\n' + library_context
                payload.update(prompt=prompt, system_prompt=SYSTEM_PROMPT)
                return payload
            def generate(request):
                response = dict(self.model_call(request))
                response['code'] = self.extract_code(response.get('text', ''), instance)
                return response
            def evaluate(task, code):
                raw = dict(self.public_evaluator(task, code))
                raw['status'] = checked_public_feedback(raw).status
                return raw
            options = {} if self.clock is None else {'clock': self.clock}
            out = Controller(generate, evaluate, self.context, plugin=self.plugin,
                             max_output=self.max_output, request_adapter=request_adapter, **options).solve(public.to_dict(), budget)
            if out['status'] == 'PUBLIC_ACCEPTED':
                self.library.add(instance, out['selected']['code'])
            return out
        finally:
            self.running = False


def baseline_manifest(root, context):
    """Pin the archived reference and this adapter; this is not server attestation."""
    root = Path(root)
    paths = [Path('experiments/flowevo_taco_lcb_20261019/evidence/benchmark.py'),
             Path('FlowEvo/src/code_math/runner.py'),
             Path('FlowEvo/src/failure_evo/native_adapter.py'),
             Path('FlowEvo/src/failure_evo/runtime.py')]
    return dict(protocol='public-feedback-adapted-v2', fingerprint=context.to_dict(),
                source='local archived benchmark; server entry/config must be confirmed separately',
                files={str(p): hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths},
                success_library='host-supplied CodeSkillLibrary; separate instance per arm',
                hidden_feedback='external final evaluation only', new_model_calls=0)
