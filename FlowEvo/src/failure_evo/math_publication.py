"""Host-only three-Gate evaluation, separate from runtime retrieval.
Private reference cases never enter parser, matcher, solver or native requests.
Independent review is a host trust boundary, not a model self-certification.
"""
import time
import jsonschema
from dataclasses import asdict
from .contracts import fingerprint
from .evidence import EvidenceStore
from .math_router import MathQuality, RoutingPolicy
from .operator_dual_validation import compare
from code_math.no_gold import PublicMathTask, NoGoldMathController, NoGoldPolicy


class MathPublicationGate:
    def __init__(self, registry, probe, private_journal, *, policy=RoutingPolicy(), engineering=False):
        self.registry, self.probe, self.policy = registry, probe, policy
        self.private = EvidenceStore(private_journal)
        self.engineering = engineering

    def freeze(self, artifact, cases, *, development_originals, input_rate, output_rate, tool_second_rate):
        ids = [x['task_id'] for x in cases]
        originals = {x['original_id'] for x in cases}
        excluded = set(development_originals) | set(artifact['excluded_task_ids'])
        if not cases or len(ids) != len(set(ids)) or originals & excluded or set(ids) & excluded:
            raise PermissionError('independent task/original split required')
        if any(x.get('review_status') != 'INDEPENDENT_VERIFIED' or not x.get('reviewer') or
               not x.get('oracle_sha256') or type(x.get('supported')) is not bool for x in cases):
            raise PermissionError('independent semantic and oracle review required')
        import math
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in (input_rate,output_rate,tool_second_rate)):
            raise ValueError('frozen nonnegative rates required')
        record = dict(artifact=artifact, cases=cases, development_originals=development_originals,
                      scope=self.probe.sha256, policy_sha256=self.policy.sha256,
                      input_rate=input_rate, output_rate=output_rate, tool_second_rate=tool_second_rate)
        key = fingerprint(record)
        if any(r['kind']=='MATH_THREE_GATE_FROZEN' and r['payload']['id']==key for r in self.private.records()):
            raise PermissionError('Gate already frozen')
        self.private.append('MATH_THREE_GATE_FROZEN',dict(id=key,**record),time.time())
        return key

    def evaluate(self, freeze_id, client, controller_journal, *, solver_policy=NoGoldPolicy(), strict_delivery=False):
        frozen = next(r['payload'] for r in self.private.records() if r['kind']=='MATH_THREE_GATE_FROZEN' and r['payload']['id']==freeze_id)
        if any(r['kind']=='MATH_THREE_GATE_STARTED' and r['payload']['id']==freeze_id for r in self.private.records()):
            raise PermissionError('consumed Gate; no silent rerun after interruption')
        if frozen['policy_sha256']!=self.policy.sha256 or frozen['scope']!=self.probe.sha256:
            raise PermissionError('frozen route changed')
        a=frozen['artifact']
        if a['origin']=='MOCK' and not self.engineering: raise PermissionError('Mock Gate')
        self.private.append('MATH_THREE_GATE_STARTED',dict(id=freeze_id),time.time())
        probe=self.probe
        class Preview:
            # Isolated pre-publication single-candidate evaluation only.
            def run(self, task, *, sequence):
                started=time.monotonic()
                try:
                    facts=probe.prepare(task);m=probe.match(a,facts)
                except (ValueError, jsonschema.ValidationError) as exc:
                    m=dict(status='UNKNOWN',reason=str(exc)[:180])
                result=probe.split.solve(a,m['parameters']) if m['status']=='MATCH' else dict(status='ERROR' if m['status']=='ERROR' else 'DECLINED',reason=m.get('reason','not matched'))
                return [dict(result,match=m,code_sha256=a['code_sha256'],operator_id=a['operator_id'],seconds=time.monotonic()-started,gold_exposed=False,**probe.usage)]
        opts=asdict(solver_policy);opts['operators_enabled']=False
        g=NoGoldMathController(client,controller_journal,policy=NoGoldPolicy(**opts))
        opts['operators_enabled']=True
        f=NoGoldMathController(client,controller_journal,policy=NoGoldPolicy(**opts),library=Preview())
        rows=[]
        def cost(lock):
            return (lock['input_tokens']*frozen['input_rate']+lock['output_tokens']*frozen['output_rate']+
                    lock['tool_seconds']*frozen['tool_second_rate'])
        def score(lock,answer):
            if not strict_delivery:return compare(lock['final_output'],answer)
            from code_math.discovery_continuation import grade_continuation
            applied=bool(lock['operator_events'] and lock['operator_events'][-1]['status']=='APPLIED')
            finish='stop' if applied else lock['responses'][-1].get('finish_reason') if lock['responses'] else None
            v=grade_continuation(lock['final_output'],answer,finish)
            return {'CONFIRMED_CORRECT':'CORRECT','CONFIRMED_WRONG':'WRONG'}.get(v['status'],v['status'])
        for i,c in enumerate(frozen['cases']):
            task=PublicMathTask(c['task_id'],c['problem'])
            gl=g.solve(task,episode_id=freeze_id+'/G/'+task.task_id,sequence=i)
            fl=f.solve(task,episode_id=freeze_id+'/F/'+task.task_id,sequence=i)
            # All gold access happens AFTER both terminal answers are locked.
            m=fl['operator_events'][-1]['match']
            computation='NOT_APPLICABLE'
            if c['supported']:
                direct=probe.split.solve(a,c['parameters'])
                computation=compare(direct['answer'],c['answer']) if direct['status']=='APPLIED' else 'ERROR'
                routing='CORRECT_ACCEPT' if m['status']=='MATCH' and m['parameters']==c['parameters'] else 'PARAMETER_ERROR' if m['status']=='MATCH' else m['status']
            else:
                routing='FALSE_ACCEPT' if m['status']=='MATCH' else 'CORRECT_REFUSAL' if m['status']=='DECLINE' else m['status']
            row=dict(task_id=task.task_id,original_id=c['original_id'],supported=c['supported'],computation=computation,
                     routing=routing,generic=score(gl,c['answer']),
                     combined=score(fl,c['answer']),fallback=fl['fallback'],
                     g_lock=gl['locked_sha256'],f_lock=fl['locked_sha256'],cost_delta=cost(fl)-cost(gl),
                     token_delta=fl['input_tokens']+fl['output_tokens']-gl['input_tokens']-gl['output_tokens'],
                     tool_seconds=fl['tool_seconds'])
            rows.append(row)
            self.private.append('MATH_THREE_GATE_ROW',dict(id=freeze_id,**row),time.time())
        positives=[r for r in rows if r['supported']];negatives=[r for r in rows if not r['supported']]
        compute=bool(positives) and all(r['computation']=='CORRECT' for r in positives)
        routing=bool(positives and negatives) and all(r['routing'] in ('CORRECT_ACCEPT','CORRECT_REFUSAL') for r in rows)
        wins={r['original_id'] for r in rows if r['combined']=='CORRECT' and r['generic']=='WRONG'}
        loss=[r for r in rows if r['generic']=='CORRECT' and r['combined']!='CORRECT']
        delta=sum((r['combined']=='CORRECT')-(r['generic']=='CORRECT') for r in rows)
        cost_delta=sum(r['cost_delta'] for r in rows)
        evaluated=all(r['generic'] in ('CORRECT','WRONG') and r['combined'] in ('CORRECT','WRONG') for r in rows)
        e2e=evaluated and not loss and (delta>0 or (delta==0 and cost_delta<0))
        coverage=len({r['original_id'] for r in positives})>=self.policy.min_distinct_originals
        summary=dict(id=freeze_id,artifact=a,scope=frozen['scope'],policy_sha256=self.policy.sha256,
                     computation_gate=compute,routing_gate=routing,end_to_end_gate=e2e,
                     independent_coverage=coverage,passed=compute and routing and e2e and coverage,
                     origin='ENGINEERING_MOCK' if self.engineering else 'REAL_EVALUATION',
                     quality=dict(winning_originals=len(wins),net_correct=delta,cost_delta=cost_delta,
                                  token_delta=sum(r['token_delta'] for r in rows),
                                  supported=len(positives),negative=len(negatives),
                                  false_accept=sum(r['routing']=='FALSE_ACCEPT' for r in rows),
                                  errors=sum(r['routing']=='ERROR' for r in rows),
                                  unknown=sum(r['routing']=='UNKNOWN' for r in rows),
                                  regression=len(loss),fallback=sum(r['fallback'] for r in rows)),
                     rows_sha256=fingerprint(rows))
        self.private.append('MATH_THREE_GATE_COMPLETED',summary,time.time())
        return summary

    def publish(self, summary):
        if not summary['passed'] or not any(r['kind']=='MATH_THREE_GATE_COMPLETED' and r['payload']==summary for r in self.private.records()):
            raise PermissionError('all three executed Gates required')
        a=summary['artifact']
        # Existing admission and future permissions remain independently necessary.
        if not any(r['kind']=='MATH_EXPERIMENTAL' and r['payload']['artifact']==a for r in self.registry.events.records()):
            raise PermissionError('existing VersionGate admission required')
        old=MathQuality(self.registry,self.policy).publications(a,summary['scope'])
        if old:
            if old[-1]!=summary:raise PermissionError('publication version conflict')
            return old[-1]
        self.registry.events.append('MATH_ROUTER_PUBLICATION',summary,time.time())
        return summary
