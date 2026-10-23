"""V2 hooks for the native controller; workers never receive learning or registry APIs."""
import ast
import copy
import hashlib
import time

from .contracts import PublicFeedback, canonical
from .failure_events import checked_public_feedback, public_check_outcome, generation_metadata, structural_status
from .failure_registry import HOOKS
from .runtime import BudgetExhausted


class FailureLearningPlugin:
    def __init__(self, registry, evidence, context, *, stream_id, experiment_id='',
                 runner=None, enabled=True, synthetic=False):
        self.registry, self.evidence, self.context = registry, evidence, context
        self.stream_id, self.experiment_id = stream_id, experiment_id
        self.runner, self.enabled, self.synthetic = runner, enabled, synthetic
        self.current = None

    def begin(self, task, at):
        if self.current is not None:
            raise RuntimeError('one task at a time per learning stream')
        completed = [r['payload'] for r in self.evidence.events.records()
                     if r['kind'] == 'TASK_COMPLETED' and r['payload']['stream_id'] == self.stream_id]
        if any(r['task_id'] == task.problem_id for r in completed):
            raise ValueError('task already completed in this stream')
        index = len(completed) + 1
        snapshot = self.registry.snapshot(stream_id=self.stream_id, task_index=index,
                                          experiment_id=self.experiment_id, at=at)
        self.current = dict(task=task, snapshot=snapshot, ledger=[], observations=[], hooks=[], attempted=set())

    def observe(self, code, stage, feedback, response, at, parent='', learnable=True):
        state = self.current
        candidate = dict(candidate_id='c' + str(len(state['ledger']) + 1), code=code,
                         code_sha256=hashlib.sha256(code.encode()).hexdigest(), parent_sha256=parent,
                         stage=stage, structural_status=structural_status(code), learnable=learnable,
                         validation_cost={'tool_calls':0,'cpu_seconds':None},
                         public_feedback=feedback.to_dict(), generation_metadata=generation_metadata(response))
        state['ledger'].append(candidate)
        state['observations'].append((candidate, at))
        return candidate

    def invoke(self, hook, checkpoint, stage, code, feedback, budget, evaluator, at):
        state = self.current
        key = (checkpoint, hook)
        if hook not in HOOKS or key in state['attempted']:
            return None
        state['attempted'].add(key)
        task, snapshot = state['task'], state['snapshot']
        try:
            names = {n.id for n in ast.walk(ast.parse(code)) if isinstance(n, ast.Name)}
        except (SyntaxError, ValueError):
            names = set()
        eligible = []
        for card in snapshot.cards:
            if hasattr(self.registry, 'reconcile'):
                try:
                    if not self.registry.reconcile(card, at):
                        continue
                except Exception:
                    state['hooks'].append(dict(hook=hook, checkpoint=checkpoint, status='error', reason='registry_reconciliation_failed'))
                    return None
            if (card.evidence_fingerprint != self.context or hook not in card.hooks or stage not in card.stages
                    or feedback.status not in card.allowed_feedback
                    or (card.structural_statuses and structural_status(code) not in card.structural_statuses)
                    or not set(card.required_ast_names) <= names
                    or not all(term.lower() in task.prompt.lower() for term in card.prompt_terms)
                    or not (card.structural_statuses or card.required_ast_names or card.prompt_terms)
                    or not self.registry.valid(card, at)):
                continue
            eligible.append(card)
        if not eligible:
            return None
        # Explicit frozen priority; tied scopes are unknown rather than cascade search.
        if len(eligible) > 1 and eligible[0].priority == eligible[1].priority:
            state['hooks'].append(dict(hook=hook, checkpoint=checkpoint, status='declined', reason='ambiguous_scope'))
            return None
        card = eligible[0]
        audit = dict(hook=hook, checkpoint=checkpoint, operator_id=card.operator_id,
                     version=card.version, snapshot_id=snapshot.snapshot_id, status='declined')
        state['hooks'].append(audit)
        if (self.runner is None or budget.remaining_seconds <= card.max_seconds + 1
                or budget.max_tools - budget.tool_calls < 3):
            audit['reason'] = 'runner_or_fallback_budget_unavailable'
            return None
        payload = dict(task_public=task.to_dict(), candidate_code=code, public_feedback=feedback.to_dict(),
                       generation_metadata=state['ledger'][-1]['generation_metadata'] if state['ledger'] else {},
                       candidate_ledger=copy.deepcopy(state['ledger']), remaining_budget=budget.snapshot(),
                       hook=hook, checkpoint_id=checkpoint, registry_snapshot_id=snapshot.snapshot_id)
        reservation = None
        if hasattr(self.registry, 'reserve_opportunity'):
            try:
                reservation = self.registry.reserve_opportunity(card, stream_id=self.stream_id,
                    experiment_id=self.experiment_id, task_index=snapshot.task_index, task_id=task.problem_id,
                    checkpoint=checkpoint, hook=hook, program_sha256=hashlib.sha256(code.encode()).hexdigest(), at=at)
                if reservation is False:
                    audit['reason'] = 'trial_quota_or_authorization_unavailable'
                    return None
            except Exception:
                audit.update(status='error', reason='trial_reservation_failed')
                return None
        started = time.monotonic()
        tools_before = budget.tool_calls
        try:
            budget.tool()
            result = self.runner.run(card, payload, min(card.max_seconds, budget.remaining_seconds))
            if budget.remaining_seconds <= 0 or time.monotonic() - started > card.max_seconds:
                raise BudgetExhausted('operator exceeded task/operator deadline')
            if not self.registry.valid(card, None):
                raise ValueError('operator authorization changed')
            if not isinstance(result, dict) or result.get('status') not in ('applied', 'declined', 'error'):
                raise ValueError('invalid operator result')
            # No permission changes, hidden scores, self-admission, or extra actions.
            allowed = {'status', 'candidate_code', 'selected_candidate_id', 'validation_status', 'actual_cost', 'evidence_ids', 'reason'}
            if set(result) - allowed or len(canonical(result).encode()) > 16384:
                audit['safety_incident'] = 'unauthorized_action'
                raise ValueError('operator attempted unauthorized action')
            if result['status'] != 'applied':
                if 'candidate_code' in result or 'selected_candidate_id' in result:
                    audit['safety_incident'] = 'action_on_non_applied_result'
                    raise ValueError('action on non-applied result')
                audit['status'] = result['status']
                return None
            audit['proposed'] = True
            if ('candidate_code' in result) == ('selected_candidate_id' in result):
                raise ValueError('exactly one action required')
            if 'candidate_code' in result:
                if 'candidate_code' not in card.allowed_actions:
                    audit['safety_incident'] = 'code_capability_unavailable'
                    raise ValueError('code capability unavailable')
                proposed = result['candidate_code']
            else:
                if 'select_candidate' not in card.allowed_actions:
                    audit['safety_incident'] = 'selection_capability_unavailable'
                    raise ValueError('selection capability unavailable')
                candidate = next((c for c in state['ledger'] if c['candidate_id'] == result['selected_candidate_id']), None)
                if candidate is None:
                    audit['safety_incident'] = 'candidate_outside_public_ledger'
                    raise ValueError('candidate is not in public ledger')
                proposed = candidate['code']
            if not isinstance(proposed, str):
                raise ValueError('candidate code must be text')
            candidate = self.observe(proposed, stage + ':operator', PublicFeedback('UNKNOWN'), {}, at,
                                     hashlib.sha256(code.encode()).hexdigest())
            if structural_status(proposed) != 'STRUCTURAL_PASS':
                raise ValueError('candidate failed structural check')
            if task.function_name:
                tree = ast.parse(proposed)
                if not any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == task.function_name for n in ast.walk(tree)):
                    raise ValueError('candidate broke required signature')
            budget.tool()
            candidate['validation_cost']['tool_calls']=1
            raw_public = evaluator(task, proposed)
            public = checked_public_feedback(raw_public)
            candidate.update(public_check_outcome(raw_public))
            audit.update(public_check_outcome(raw_public))
            if budget.remaining_seconds <= 0:
                raise BudgetExhausted('validation exceeded task deadline')
            candidate['public_feedback'] = public.to_dict()
            audit['validation_status'] = 'public_tests_pass' if public.status == 'PUBLIC_PASS' else ('structural_pass' if audit['public_check_outcome']=='unavailable' else 'failed')
            if not self.registry.valid(card, None):
                raise ValueError('operator authorization changed during public validation')
            if public.status != 'PUBLIC_PASS':
                if feedback.status == 'PUBLIC_PASS' and audit['public_check_outcome'] == 'failed':
                    audit['safety_incident'] = 'host_verified_negative_transfer'
                audit.update(status='declined', reason='host_public_validation_failed')
                return None
            audit.update(status='applied', candidate_id=candidate['candidate_id'])
            return dict(stage=stage, code=proposed, code_sha256=candidate['code_sha256'], public_feedback=public)
        except Exception as exc:
            audit.update(status='error', reason=type(exc).__name__)
            return None
        finally:
            audit['actual_cost'] = dict(tool_calls=budget.tool_calls-tools_before, elapsed_seconds=time.monotonic()-started, model_calls=0, model_tokens=0)
            try:
                if audit.get('safety_incident') and hasattr(self.registry, 'suspend'):
                    self.registry.suspend(card, audit['safety_incident'], at)
                if reservation:
                    audit['synthetic'] = self.synthetic
                    self.registry.complete_opportunity(card, reservation, outcome=audit, at=at)
            except Exception:
                # Reserved quota is never refunded after a crash or failed audit write.
                audit.update(status='error', reason='registry_outcome_write_failed')
                return None

    def finish(self, at):
        state = self.current
        if state is None:
            return
        try:
            for candidate, observed in state['observations']:
                if not candidate['learnable']:
                    continue
                # Already projected by the host; retain its audited cases.
                raw = candidate['public_feedback']
                feedback = PublicFeedback(raw['status'], raw['summary'], tuple(canonical(c) for c in raw['public_cases']))
                self.evidence.record(stream_id=self.stream_id, task_id=state['task'].problem_id,
                    family_id='artifact_recovery' if candidate['structural_status'] != 'STRUCTURAL_PASS' else 'public_failure',
                    stage=candidate['stage'], code=candidate['code'], feedback=feedback,
                    observed_at=observed, available_from=at,
                    finish_reason=candidate['generation_metadata']['finish_reason'],
                    parent_sha256=candidate['parent_sha256'], synthetic=self.synthetic, validation_cost=candidate['validation_cost'])
            self.evidence.events.append('TASK_COMPLETED', dict(stream_id=self.stream_id,
                task_id=state['task'].problem_id, task_index=state['snapshot'].task_index,
                snapshot_id=state['snapshot'].snapshot_id), at)
        finally:
            self.current = None
