"""Default-off, single-controller math routing on the existing VersionGate journal.

No domain keywords, model calls, or private answers in this module. Host-reviewed
Gate summaries are necessary in addition to the existing finite trial permission.
The evidence journal is trusted host infrastructure, never writable by operators.
"""
from dataclasses import dataclass, asdict
import json
import time
import math
import hashlib
from pathlib import Path
import jsonschema
from .contracts import fingerprint, canonical
from .semantic_contract import SplitRunner
from .semantic_evidence_v2 import validate_packet

VERSION = 'math-router-v1'

@dataclass(frozen=True)
class RoutingPolicy:
    max_candidates: int = 8
    max_worker_calls: int = 9
    max_seconds: float = 30.0
    min_distinct_originals: int = 2

    def __post_init__(self):
        if (type(self.max_candidates) is not int or self.max_candidates < 1 or
                type(self.max_worker_calls) is not int or self.max_worker_calls < 2 or
                not math.isfinite(self.max_seconds) or self.max_seconds <= 0 or
                type(self.min_distinct_originals) is not int or self.min_distinct_originals < 2):
            raise ValueError('bounded routing policy required')

    @property
    def sha256(self):
        dependencies=['math_router.py','math_publication.py','semantic_contract.py','semantic_evidence_v2.py','operator_version_gate.py']
        source={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in dependencies}
        return fingerprint(dict(version=VERSION, implementation=source, **asdict(self)))


class MathQuality:
    """Scope/version-bound host evidence. Missing evidence is not a success."""
    def __init__(self, registry, policy=RoutingPolicy()):
        self.registry, self.events, self.policy = registry, registry.events, policy

    def freeze_feedback_roles(self, roles):
        """Predeclare feedback visibility before any task invocation."""
        if not roles or any(not k or v not in ('ONLINE_POST_TASK','SEALED_GOVERNANCE') for k,v in roles.items()):
            raise ValueError('feedback roles')
        records=self.events.records()
        existing={k:v for r in records if r['kind']=='MATH_FEEDBACK_ROLES' for k,v in r['payload'].items()}
        for k,v in roles.items():
            if k in existing and existing[k]!=v: raise PermissionError('immutable task role')
            if any(r['kind']=='MATH_ROUTE_STARTED' and r['payload']['task_id']==k for r in records):
                raise PermissionError('role cannot be assigned after execution')
        self.events.append('MATH_FEEDBACK_ROLES',roles,time.time())

    def feedback_role(self, task_id):
        roles={k:v for r in self.events.records() if r['kind']=='MATH_FEEDBACK_ROLES' for k,v in r['payload'].items()}
        return roles.get(task_id)

    def publications(self, artifact, scope):
        return [r['payload'] for r in self.events.records()
                if r['kind'] == 'MATH_ROUTER_PUBLICATION'
                and r['payload']['artifact'] == artifact
                and r['payload']['scope'] == scope
                and r['payload']['policy_sha256'] == self.policy.sha256]

    def summary(self, artifact, scope, sequence):
        pubs = self.publications(artifact, scope)
        rows = [r['payload'] for r in self.events.records()
                if r['kind'] == 'MATH_REUSE_OUTCOME'
                and r['payload']['code_sha256'] == artifact['code_sha256']
                and r['payload']['scope'] == scope
                and r['payload']['visibility'] == 'ONLINE_POST_TASK'
                and r['payload']['available_after'] < sequence]
        # Repeated runs of one original cannot manufacture independent evidence.
        by_original = {}
        for row in rows:
            by_original.setdefault(row['original_id'], []).append(row)
        paired = [r for r in rows if r['generic_correct'] is not None]
        wins = sum(any(x['correct'] is True and x['generic_correct'] is False for x in rs)
                   for rs in by_original.values())
        losses = sum(any(x['correct'] is False and x['generic_correct'] is True for x in rs)
                     for rs in by_original.values())
        return dict(publication=pubs[-1] if pubs else None, uses=len(rows),
                    distinct_originals=len(by_original), wins=wins, losses=losses,
                    correct=sum(r['correct'] is True for r in rows),
                    errors=sum(r['execution_status'] == 'ERROR' for r in rows),
                    unknown=sum(r['correct'] is None for r in rows),
                    paired_uses=len(paired),
                    token_delta=sum(r['token_delta'] for r in paired),
                    cost_delta=sum(r['cost_delta'] for r in paired),
                    tool_seconds=sum(r['tool_seconds'] for r in rows),
                    unknown_cost_uses=sum(not r['cost_verified'] for r in rows),
                    instability=sum(len({x['correct'] for x in rs if x['correct'] is not None}) > 1
                                    for rs in by_original.values()))

    def rank(self, a, scope, sequence):
        q = self.summary(a, scope, sequence)
        p = q['publication']
        if p is None:
            raise PermissionError('three Gates absent')
        g = p['quality']
        # Correctness/negative transfer first; paired cost only after reliability.
        return (-q['losses'], -q['errors'], -q['instability'],
                q['wins'] + g['winning_originals'],
                g['net_correct'], -q['cost_delta'] - g['cost_delta'])

    def record_outcome(self, artifact, scope, locked, verdict, *, controller,
                       scorer, original_id, cost, generic=None, generic_verdict=None,
                       generic_cost=0.0, visibility='ONLINE_POST_TASK'):
        """Called only after durable answer lock and independent host scoring.
        `controller` and `scorer` are host EvidenceStores. Sealed outcomes cannot
        update ranking; explicit governance suspension is a separate operation.
        """
        if visibility not in ('ONLINE_POST_TASK', 'SEALED_GOVERNANCE') or self.feedback_role(locked['task_id']) != visibility:
            raise ValueError('visibility')
        if not original_id or any(type(x) not in (float, int) or not math.isfinite(x) or x < 0
                                  for x in (cost, generic_cost) if x is not None):
            raise ValueError('identity/cost')
        def verify(lock, grade):
            if not any(r['kind'] == 'MATH_ANSWER_LOCKED' and r['payload'] == lock for r in controller.records()):
                raise PermissionError('unrecorded lock')
            if not any(r['kind'] == 'MATH_PRIVATE_SCORE' and r['payload'] == grade for r in scorer.records()):
                raise PermissionError('unrecorded score')
            if grade['locked_sha256'] != lock['locked_sha256'] or grade['task_id'] != lock['task_id']:
                raise PermissionError('score binding')
            if fingerprint({k:v for k,v in lock.items() if k != 'locked_sha256'}) != lock['locked_sha256']:
                raise PermissionError('altered lock')
            return True if grade['correct'] else False if grade['credible_failure'] else None
        correct = verify(locked, verdict)
        executions = [r['payload'] for r in self.events.records() if r['kind'] == 'MATH_ROUTER_EXECUTED'
                      and r['payload']['task_id'] == locked['task_id']
                      and r['payload']['sequence'] == locked['sequence']
                      and r['payload']['code_sha256'] == artifact['code_sha256']
                      and r['payload']['scope'] == scope]
        if not executions or executions[-1]['result'] not in locked['operator_events']:
            raise PermissionError('no bound actual invocation')
        gc = None
        if generic is not None:
            if generic['task_id'] != locked['task_id'] or generic['operator_events'] or generic['protocol'] != locked['protocol']:
                raise PermissionError('noncomparable Generic')
            starts = [r['payload'] for r in controller.records() if r['kind'] == 'MATH_TASK_STARTED']
            own = next(x for x in starts if x['episode_id'] == locked['episode_id'])
            other = next(x for x in starts if x['episode_id'] == generic['episode_id'])
            if not own.get('problem_sha256') or own['problem_sha256'] != other.get('problem_sha256'):
                raise PermissionError('paired task mismatch')
            opolicy, gpolicy = dict(own['policy']), dict(other['policy'])
            opolicy.pop('operators_enabled', None); gpolicy.pop('operators_enabled', None)
            if opolicy != gpolicy: raise PermissionError('paired policy mismatch')
            gc = verify(generic, generic_verdict)
        key = fingerprint([locked['locked_sha256'], artifact['code_sha256'], scope])
        old = [r['payload'] for r in self.events.records() if r['kind'] == 'MATH_REUSE_OUTCOME' and r['payload']['id'] == key]
        row = dict(id=key, code_sha256=artifact['code_sha256'], scope=scope,
                   task_id=locked['task_id'], original_id=original_id,
                   available_after=locked['sequence'], visibility=visibility,
                   correct=correct if executions[-1]['result']['status']=='APPLIED' else None, generic_correct=gc,
                   execution_status=executions[-1]['result']['status'],
                   token_delta=(locked['input_tokens']+locked['output_tokens']-generic['input_tokens']-generic['output_tokens']) if gc is not None else 0,
                   cost_delta=cost-generic_cost if gc is not None and cost is not None and generic_cost is not None else 0,
                   cost_verified=cost is not None and (gc is None or generic_cost is not None),
                   estimated_cost=cost, tool_seconds=locked['tool_seconds'],
                   locked_sha256=locked['locked_sha256'], score_sha256=fingerprint(verdict))
        if old:
            if old[0] != row: raise PermissionError('conflicting outcome replay')
            return old[0]
        self.events.append('MATH_REUSE_OUTCOME', row, time.time())
        if visibility == 'ONLINE_POST_TASK' and (correct is False or row['execution_status'] == 'ERROR'):
            self.registry.suspend(artifact['code_sha256'], 'verified reuse failure; '+key)
        return row

    def governance_suspend(self, artifact, outcome_id):
        if not any(r['kind'] == 'MATH_REUSE_OUTCOME' and r['payload']['id'] == outcome_id
                   and r['payload']['code_sha256'] == artifact['code_sha256']
                   and r['payload']['visibility'] == 'SEALED_GOVERNANCE'
                   and r['payload']['correct'] is False for r in self.events.records()):
            raise PermissionError('sealed negative governance receipt required')
        self.registry.suspend(artifact['code_sha256'], 'external sealed governance: '+outcome_id)


class StructuredCandidateProbe:
    """One shared, provenance-bound parse; inspect all candidates before solving.
    parser(task) returns (packet, provenance); it must use the existing budgeted
    transport. No private/reference semantic input is accepted at runtime.
    """
    def __init__(self, split, semantics, parser, *, parser_identity, allow_mock=False):
        if not isinstance(split, SplitRunner): raise TypeError('existing Linux runner required')
        self.split, self.semantics, self.parser = split, semantics, parser
        if not parser_identity or not isinstance(parser_identity,dict): raise ValueError('frozen parser identity required')
        self.semantic_sha256 = fingerprint(semantics)
        self.sha256 = fingerprint(dict(semantics=self.semantic_sha256,parser=parser_identity))
        self.allow_mock=allow_mock
        self.usage={}

    def prepare(self, task):
        self.usage={}
        packet, provenance = self.parser(task)
        origin=provenance.get('model_origin')
        if origin not in ('GPT','DEEPSEEK','MOCK') or (origin=='MOCK' and not self.allow_mock):
            raise PermissionError('parser model origin')
        usage=provenance.get('usage',{})
        if set(usage)!={'prompt_tokens','completion_tokens','reasoning_tokens','model_calls'} or any(type(x) is not int or x<0 for x in usage.values()):
            raise ValueError('parser usage required')
        self.usage=dict(routing_input_tokens=usage['prompt_tokens'],routing_output_tokens=usage['completion_tokens'],routing_reasoning_tokens=usage['reasoning_tokens'],routing_model_calls=usage['model_calls'])
        if (provenance.get('origin') != 'MODEL_PARSE' or
            provenance.get('problem_sha256') != fingerprint(task.problem) or
            provenance.get('parsed_sha256') != fingerprint(packet) or
            not provenance.get('response_sha256') or packet.get('task_id') != task.task_id):
            raise ValueError('unbound runtime parse')
        facts = validate_packet(self.semantics, task.problem, packet)
        if packet['review']['status'] != 'NO_ISSUE_OBSERVED': raise ValueError('uncertain review')
        objective = facts.get('requested_quantity')
        if not isinstance(objective, str) or not objective or objective == 'UNKNOWN':
            raise ValueError('unknown objective')
        return facts

    def match(self, a, facts):
        if a['provenance'].get('semantics_sha256') != self.semantic_sha256: raise ValueError('schema version mismatch')
        required = a['provenance'].get('required_facts', [])
        if not required or any(facts.get(k) is None for k in required):
            return dict(status='UNKNOWN', reason='unconfirmed premise')
        raw = self.split.component(a, 'match', facts)
        v = raw.get('value')
        fields = {'status','parameters','reason','assumption_quotes','requested_quantity'}
        if (raw.get('status') != 'OK' or not isinstance(v, dict) or set(v) != fields or
            len(canonical(v)) > 16384 or v['status'] not in ('MATCH','DECLINE','UNKNOWN') or
            not isinstance(v['reason'], str) or not isinstance(v['parameters'], dict) or v['assumption_quotes'] != []):
            return dict(status='ERROR', reason='matcher contract')
        if v['status'] == 'MATCH':
            if v['requested_quantity'] != facts['requested_quantity'] or v['requested_quantity'] != a['contract']['requested_quantity']:
                return dict(status='UNKNOWN', reason='objective conflict')
            jsonschema.validate(v['parameters'], json.loads(a['contract']['parameter_schema']))
        return v


class UnifiedMathRouter:
    """Drop-in .run for NoGoldMathController; no model/gold-driven rescue.
    Single writer, fail closed on candidate overflow or unresolved top-score tie.
    """
    def __init__(self, registry, probe, *, policy=RoutingPolicy(), engineering=False):
        self.registry, self.probe, self.policy = registry, probe, policy
        self.quality, self.engineering = MathQuality(registry, policy), engineering
        if not engineering and (probe.split.budget is None or probe.allow_mock):
            raise PermissionError('PersistentBudget required for real routing')

    def record_feedback(self, task, locked, verdict, *, controller, scorer, original_id, cost=None):
        """Host scoring hook; no paired baseline means no causal win claim."""
        executions=[r['payload'] for r in self.registry.events.records()
                    if r['kind']=='MATH_ROUTER_EXECUTED' and r['payload']['task_id']==task.task_id
                    and r['payload']['sequence']==locked['sequence']]
        if not executions: return None
        execution=executions[-1]
        a=next(r['payload']['artifact'] for r in self.registry.events.records()
               if r['kind']=='MATH_ROUTER_PUBLICATION' and r['payload']['artifact']['code_sha256']==execution['code_sha256'])
        return self.quality.record_outcome(a,execution['scope'],locked,verdict,
                    controller=controller,scorer=scorer,original_id=original_id,cost=cost,
                    visibility=self.quality.feedback_role(task.task_id))

    def run(self, task, *, sequence):
        started = time.monotonic()
        self.probe.usage={}
        scope = self.probe.sha256
        decision = dict(task_id=task.task_id, problem_sha256=fingerprint(task.problem),
                        sequence=sequence, scope=scope, policy_sha256=self.policy.sha256, candidates=[])
        def fallback(reason):
            decision['reason'] = reason
            self.registry.events.append('MATH_ROUTER_DECISION', decision, time.time())
            return [dict(status='DECLINED', reason=reason, seconds=time.monotonic()-started, gold_exposed=False,**self.probe.usage)]
        eligible = [a for a in self.registry.eligible(task, sequence)
                    if self.quality.publications(a, scope)]
        if not eligible: return fallback('NO_QUALIFIED_CANDIDATE')
        if self.quality.feedback_role(task.task_id) is None: return fallback('UNFROZEN_FEEDBACK_ROLE')
        if len(eligible) > self.policy.max_candidates or len(eligible)+1 > self.policy.max_worker_calls:
            return fallback('RETRIEVAL_RESOURCE_LIMIT')
        if any(a['origin'] == 'MOCK' or self.quality.publications(a, scope)[-1]['origin']=='ENGINEERING_MOCK' for a in eligible) and not self.engineering:
            raise PermissionError('Mock cannot enter real tasks')
        # Durable task/sequence reservation prevents duplicate probes after crash.
        key = fingerprint([task.task_id, sequence])
        if any(r['kind'] == 'MATH_ROUTE_STARTED' and r['payload']['id'] == key for r in self.registry.events.records()):
            raise PermissionError('route already consumed; audit before resume')
        self.registry.events.append('MATH_ROUTE_STARTED', dict(id=key, **decision), time.time())
        try: facts = self.probe.prepare(task)
        except (ValueError, jsonschema.ValidationError) as exc: return fallback('SEMANTICS_UNKNOWN:'+str(exc)[:180])
        matched = []
        for a in sorted(eligible, key=lambda x:x['code_sha256']):
            if time.monotonic()-started >= self.policy.max_seconds: return fallback('TIME_LIMIT')
            self.registry.claim_trial(a, task, sequence)
            try: m = self.probe.match(a, facts)
            except (ValueError, jsonschema.ValidationError) as exc: m = dict(status='UNKNOWN', reason=str(exc)[:180])
            rank = self.quality.rank(a, scope, sequence)
            decision['candidates'].append(dict(code_sha256=a['code_sha256'], match=m, rank=rank))
            if m['status'] == 'MATCH': matched.append((rank,a,m))
            elif m['status'] == 'ERROR':
                self.registry.suspend(a['code_sha256'], 'matcher execution/contract error')
        if not matched: return fallback('NO_CONFIRMED_MATCH')
        matched.sort(key=lambda x:x[0], reverse=True)
        if len(matched)>1 and matched[0][0] == matched[1][0]: return fallback('UNRESOLVED_QUALITY_TIE')
        if time.monotonic()-started >= self.policy.max_seconds: return fallback('TIME_LIMIT')
        _, a, m = matched[0]
        result = dict(self.probe.split.solve(a,m['parameters']),match=m,
                      code_sha256=a['code_sha256'], operator_id=a['operator_id'],
                      seconds=time.monotonic()-started, gold_exposed=False,**self.probe.usage)
        decision['selected'] = a['code_sha256']
        self.registry.events.append('MATH_ROUTER_DECISION', decision, time.time())
        self.registry.events.append('MATH_ROUTER_EXECUTED',dict(task_id=task.task_id,sequence=sequence,
                    scope=scope,code_sha256=a['code_sha256'],result=result),time.time())
        if result['status']=='ERROR': self.registry.suspend(a['code_sha256'], 'solver execution error')
        return [result]
