"""Source-only B study: analyze evidence separately, merge hypotheses, compile policies."""
import json
import time
from pathlib import Path

from alfworld_.failure_learning import SOURCE_CONTRACT, register_environment_candidate, static_check
from alfworld_.skill_acquisition import (
    INPUT_LIMIT, MODEL, _has_instance_literals, import_source_events, review_source,
)
from failure_evo.autonomous_generation import DeepSeekCompilerAdapter
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_registry import FailureOperator
from failure_evo.math_skill_transfer import replay_train_generation
from failure_evo.math_stream import save

VERSION = 'alfworld-recovery-acquisition-v5'
BATCH_SIZE = 8
MAX_CANDIDATES = 4
MAX_CHECKPOINTS = 3

MIN_GROUNDED_HYPOTHESES = 2
ANALYSIS_PROMPT = """Analyze each public trajectory independently. Steps are
[step_id, action, observed feedback, was_admissible], in time order. The
failure_step_id is the failed native action, not a root cause. Copy only
IDs from this trajectory. Recovery IDs must be strictly after that anchor.
Output JSON {"analyses":[{"evidence_id":"...", "decision":"HYPOTHESIS or ABSTAIN",
"failure_evidence_id":"the provided failure_step_id",
"recovery_evidence_ids":["a provided later step_id"],
"cause":"...", "repair":"...", "uncertainty":"..."}]}.
One analysis per evidence ID. Use 1–2 different recovery IDs for HYPOTHESIS.
ABSTAIN may use an empty list. Keep each text field under 240 characters.
Do not quote or reconstruct feedback in the reference fields.
Do not infer causality from the final win alone."""
MERGE_PROMPT = """Group by the causal precondition, the intended task transition, and the
observable effect of the repair. First compare different object or target names as possible
bindings of the same roles. Prefer one parameterized mechanism if the evidence supports the
same precondition, repair order and resulting transition across bindings. A different entity
name alone is not a reason to split. The same symptom alone is not a reason to merge.
In compatibility, cite supporting receipts and identify which details can vary and which must
hold. In required_state, specify how to identify the intended object and target, even if the
blocked action is absent from admissible commands. Keep separate or leave unassigned when
preconditions, recovery, effect or required evidence differ or are uncertain. Singletons and
abstention are valid. Each assigned ID can support one mechanism. No priority ranking or source selection
from outside these records. Return JSON {"mechanisms":[{"evidence_ids":["..."],"cause":"...",
"compatibility":"why these actual receipts support one mechanism, and limitations",
"trigger":"...","required_state":"...","action_policy":"...","decline":"...",
"expected_change":"...","scope":"..."}],"uncertainty":"why any proposals were withheld"}.
An empty mechanisms list is valid. No permission, verification or correctness claims."""


RECOVERY_SOURCE_CONTRACT = SOURCE_CONTRACT + """
Ground the intended object, target and relevant phase in the public goal, observations,
history and legal commands. Bind instance identifiers dynamically. A missing blocked
command may be evidence of the precondition; do not require it to be admissible already.
Decline on ambiguity, wrong phase, missing evidence or lack of progress. An admissible
action by itself does not establish relevance. Never choose the first available action as
a fallback, act on a distractor, or repeatedly apply an action without verified progress.
When the selected mechanism is shared across bindings, implement the shared relation
instead of copying separate named-object rules. Keep scope within the evidence.
"""


def _text(value, bound):
    return isinstance(value, str) and 0 < len(value.strip()) <= bound


def parse_analyses(value, events):
    """Frozen v2 parser retained for read-only historical audits."""
    ids = {e['evidence_id']:e for e in events}
    if not isinstance(value, dict) or set(value) != {'analyses'} or not isinstance(value['analyses'], list):
        raise ValueError('invalid analyses envelope')
    found = {}
    for item in value['analyses']:
        if (not isinstance(item, dict) or set(item) !=
                {'evidence_id','decision','failure','recovery','cause','repair','uncertainty'}
                or not _text(item['evidence_id'], 64)
                or item['evidence_id'] not in ids or item['evidence_id'] in found
                or item['decision'] not in ('HYPOTHESIS','ABSTAIN')
                or not all(_text(item[k],240) for k in ('cause','repair','uncertainty'))
                or not isinstance(item['recovery'], list) or len(item['recovery']) > 2
                or (item['decision']=='HYPOTHESIS' and not item['recovery'])):
            raise ValueError('invalid or duplicate trajectory analysis')
        event = ids[item['evidence_id']]
        for i, ref in enumerate([item['failure'], *item['recovery']]):
            if (not isinstance(ref, dict) or set(ref) != {'step','quote'}
                    or type(ref['step']) is not int or not _text(ref['quote'], 180)
                    or (ref['step'] != event['anchor'] if i == 0 else
                        not event['anchor'] < ref['step'] <= len(event['steps']))
                    or ref['quote'] not in event['steps'][ref['step']-1][1]):
                raise ValueError('analysis reference is not grounded in public feedback')
        if len({r['step'] for r in item['recovery']}) != len(item['recovery']):
            raise ValueError('duplicate recovery step')
        found[item['evidence_id']] = item
    if set(found) != set(ids):
        raise ValueError('each frozen event requires its own analysis')
    return dict(analyses=[found[eid] for eid in ids])


def step_id(event, step):
    return f"{event['evidence_id'][:12]}:step_{step:03d}"


def recovery_view(event, commands):
    return dict(event, failure_step_id=step_id(event,event['anchor']),
                steps=[[step_id(event,i),*step] for i,step in enumerate(event['steps'],1)],
                anchor_admissible_commands=commands)


def _hydrate_analysis(item, event):
    if (set(item) != {'evidence_id','decision','failure_evidence_id','recovery_evidence_ids',
                      'cause','repair','uncertainty'}
            or item['decision'] not in ('HYPOTHESIS','ABSTAIN')
            or not all(_text(item[k],240) for k in ('cause','repair','uncertainty'))):
        raise ValueError('INVALID_ANALYSIS_FIELDS')
    refs = item['recovery_evidence_ids']
    if (not isinstance(refs,list) or len(refs)>2 or not all(_text(r,64) for r in refs)
            or (item['decision']=='HYPOTHESIS' and not refs)):
        raise ValueError('INVALID_RECOVERY_REFERENCES')
    if len(set(refs))!=len(refs):
        raise ValueError('DUPLICATE_RECOVERY_REFERENCE')
    anchor = event['anchor']
    if item['failure_evidence_id']!=step_id(event,anchor):
        raise ValueError('FAILURE_REFERENCE_NOT_ANCHOR')
    lookup = {step_id(event,i):(i,step) for i,step in enumerate(event['steps'],1)}

    def resolve(ref):
        i, (action, observation, admissible) = lookup[ref]
        return dict(step_id=ref,step=i,action=action,quote=observation,was_admissible=admissible)

    for ref in refs:
        if ref not in lookup:
            raise ValueError('RECOVERY_REFERENCE_UNKNOWN_OR_FOREIGN')
        if lookup[ref][0]<=anchor:
            raise ValueError('RECOVERY_REFERENCE_NOT_AFTER_FAILURE')
    return dict(evidence_id=item['evidence_id'],decision=item['decision'],cause=item['cause'],
                repair=item['repair'],uncertainty=item['uncertainty'],
                failure=resolve(item['failure_evidence_id']),recovery=[resolve(ref) for ref in refs])


def parse_step_analyses(value, events):
    """Quarantine bad or ambiguous rows while retaining grounded rows."""
    if not isinstance(value,dict) or set(value)!={'analyses'} or not isinstance(value['analyses'],list):
        raise ValueError('invalid analyses envelope')
    by_id = {e['evidence_id']:[] for e in events}
    rejected = []
    for index,item in enumerate(value['analyses'],1):
        eid = item.get('evidence_id') if isinstance(item,dict) else None
        if not isinstance(eid,str) or eid not in by_id:
            rejected.append(dict(response_row=index,reason='UNKNOWN_OR_MISSING_EVIDENCE_ID'))
        else:
            by_id[eid].append((index,item))
    accepted = []
    for event in events:
        eid = event['evidence_id']
        rows = by_id[eid]
        if len(rows)!=1:
            rejected.append(dict(evidence_id=eid,response_rows=[i for i,_ in rows],
                                 reason='DUPLICATE_ANALYSIS' if rows else 'MISSING_ANALYSIS'))
            continue
        index,item = rows[0]
        try:
            accepted.append(_hydrate_analysis(item,event))
        except ValueError as exc:
            rejected.append(dict(evidence_id=eid,response_row=index,reason=str(exc)))
    return dict(analyses=accepted,rejected=rejected)


MECHANISM_FIELDS = ('cause','compatibility','trigger','required_state','action_policy',
                    'decline','expected_change','scope')


MECHANISM_LIMITS = {field: (1000 if field=='compatibility' else 600) for field in MECHANISM_FIELDS}
UNCERTAINTY_LIMIT = 1000
EVIDENCE_ID_LENGTH = 64
MAX_MECHANISM_ROWS = 16
MECHANISM_SCHEMA = dict(type='object',additionalProperties=False,required=['mechanisms','uncertainty'],
    properties=dict(uncertainty=dict(type='string',minLength=1,maxLength=UNCERTAINTY_LIMIT),
        mechanisms=dict(type='array',maxItems=MAX_MECHANISM_ROWS,items=dict(type='object',
            additionalProperties=False,required=['evidence_ids',*MECHANISM_FIELDS],
            properties=dict(evidence_ids=dict(type='array',minItems=1,maxItems=MAX_MECHANISM_ROWS,
                uniqueItems=True,items=dict(type='string',minLength=EVIDENCE_ID_LENGTH,maxLength=EVIDENCE_ID_LENGTH)),
                **{field:dict(type='string',minLength=1,maxLength=bound)
                   for field,bound in MECHANISM_LIMITS.items()})))))


def parse_mechanisms(value, analyses):
    if not isinstance(value,dict) or set(value)!={'mechanisms','uncertainty'}:
        raise ValueError('merge: expected exactly mechanisms and uncertainty')
    if not isinstance(value['mechanisms'],list) or len(value['mechanisms'])>MAX_MECHANISM_ROWS:
        raise ValueError(f'mechanisms: expected array of at most {MAX_MECHANISM_ROWS} rows')
    if not _text(value['uncertainty'],UNCERTAINTY_LIMIT):
        raise ValueError(f'uncertainty: expected 1–{UNCERTAINTY_LIMIT} nonblank characters after trimming')
    eligible = {a['evidence_id'] for a in analyses if a['decision']=='HYPOTHESIS'}
    valid = []
    rejected = []
    claims = {}
    for i,item in enumerate(value['mechanisms']):
        path = f'mechanisms[{i}]'
        errors = []
        if not isinstance(item,dict):
            rejected.append(dict(index=i,errors=[dict(field=path,reason='expected object')]))
            continue
        allowed = {'evidence_ids',*MECHANISM_FIELDS}
        for key in sorted(allowed-set(item)):
            errors.append(dict(field=f'{path}.{key}',reason='missing required field'))
        for key in sorted(set(item)-allowed):
            errors.append(dict(field=f'{path}.{key}',reason='unexpected field'))
        for field,bound in MECHANISM_LIMITS.items():
            if field in item and not _text(item[field],bound):
                actual = len(item[field].strip()) if isinstance(item[field],str) else None
                errors.append(dict(field=f'{path}.{field}',reason='invalid text length or type',
                                   actual_length=actual,max_length=bound))
        ids = item.get('evidence_ids')
        if 'evidence_ids' in item:
            if not isinstance(ids,list) or not 1<=len(ids)<=MAX_MECHANISM_ROWS:
                errors.append(dict(field=f'{path}.evidence_ids',reason='invalid array length or type'))
            else:
                seen = set()
                for j,eid in enumerate(ids):
                    if not isinstance(eid,str) or len(eid)!=EVIDENCE_ID_LENGTH or eid not in eligible or eid in seen:
                        errors.append(dict(field=f'{path}.evidence_ids[{j}]',
                                           reason='unknown, abstained, malformed or duplicate evidence ID'))
                    if isinstance(eid,str):
                        seen.add(eid)
        if errors:
            rejected.append(dict(index=i,errors=errors))
        else:
            valid.append((i,item))
            for eid in ids:
                claims.setdefault(eid,[]).append(i)
    accepted = []
    for i,item in valid:
        collisions = [eid for eid in item['evidence_ids'] if len(claims[eid])>1]
        if collisions:
            rejected.append(dict(index=i,errors=[dict(field=f'mechanisms[{i}].evidence_ids',
                reason='ambiguous assignment across valid rows',evidence_ids=collisions)]))
        else:
            accepted.append(item)
    return dict(mechanisms=accepted,uncertainty=value['uncertainty'],
                rejected=sorted(rejected,key=lambda row:row['index']))


MERGE_FORMAT = ('\nDelivery contract. Return only JSON, no Markdown. Text lengths are checked after '
    'trimming and text must be nonblank. Copy exact eligible evidence IDs, unique within and across '
    'mechanisms. Follow this schema: '+canonical(MECHANISM_SCHEMA))


class RecoveryAdapter(DeepSeekCompilerAdapter):
    protocol = VERSION

    def __init__(self, *args, stage, payload, parser, protocol=VERSION, generation_requirements='', **kwargs):
        super().__init__(*args, **kwargs)
        self.stage = stage
        self.protocol = protocol
        self.generation_requirements = generation_requirements
        self.payload = canonical(payload)
        self.hypothesis_parser = parser

    def preflight(self, request):
        self._authorize()
        phase = 'candidate' if self.stage=='generate' else 'induction'
        if (request['phase'] != phase or request['discovery'] != {'stage': self.stage,
                'payload_sha256':fingerprint(json.loads(self.payload))}
                or (phase=='candidate' and request.get('specification') != self.payload+'\n')):
            raise PermissionError('recovery stage payload drift')
        system = {'analyze':ANALYSIS_PROMPT,'merge':MERGE_PROMPT+MERGE_FORMAT,'generate':RECOVERY_SOURCE_CONTRACT+self.generation_requirements}[self.stage]
        wire = dict(model=self.model, messages=[dict(role='system',content=system),
                    dict(role='user',content=self.payload)], max_tokens=request['max_tokens'],temperature=0,
                    thinking={'type':'disabled'},reasoning_effort='none',
                    response_format={'type':'json_object'},stream=False)
        if len(canonical(wire).encode()) + 256 > self.max_wire_input_upper:
            raise ValueError('EVIDENCE_REPRESENTATION_LIMIT')
        return wire


def stage_request(root, name, stage, payload, parser, budget, *, sender=None, authorization=None, network_policy=None,
                  protocol=VERSION, generation_requirements=''):
    """Each stage uses a frozen job with the same durable budget and provider journal."""
    adapter = RecoveryAdapter(root/'provider.jsonl', budget, model=MODEL, mock=sender is not None,
        sender=sender, authorization=authorization, network_policy=network_policy,
        stage=stage, payload=payload, parser=parser, max_wire_input_upper=INPUT_LIMIT,
        protocol=protocol,generation_requirements=generation_requirements)
    compiler = BoundedCompiler(adapter, budget, root/name/'compiler.jsonl', MODEL, max_input_upper=INPUT_LIMIT)
    job = dict(stream_id=budget.config['run_id'],family_id=fingerprint([protocol,name,payload] if not generation_requirements else
                                     [protocol,name,payload,generation_requirements]),
               discovery=dict(stage=stage,payload_sha256=fingerprint(payload)))
    if stage=='generate':
        # Import the model's checked merge proposal; no source or validation result is imported.
        spec = root/name/'model_mechanism.json'
        save(spec, payload)
        if not compiler.events.records():
            compiler.import_specification(job,spec,time.time())
        return replay_train_generation(compiler,dict(job,specification=spec.read_text()), 'candidate')
    return replay_train_generation(compiler,job,'induction')


def rank_mechanisms(merged, analyses):
    """Prefer distinct grounded sources, then distinct cited recovery observations."""
    position = {a['evidence_id']:i for i,a in enumerate(analyses)}
    by_id = {a['evidence_id']:a for a in analyses}
    ranked = []
    for proposal in merged['mechanisms']:
        ids = sorted(proposal['evidence_ids'], key=position.__getitem__)
        proposal = dict(proposal, evidence_ids=ids)
        recovery_count = sum(len(by_id[eid]['recovery']) for eid in ids)
        ranked.append(dict(mechanism_id=fingerprint(proposal), proposal=proposal, support_count=len(ids),
                           recovery_reference_count=recovery_count,
                           checkpoints=[dict(by_id[eid]['failure'], evidence_id=eid)
                                        for eid in ids[:MAX_CHECKPOINTS]]))
    ranked.sort(key=lambda x:(-x['support_count'],-x['recovery_reference_count'],
                              position[x['proposal']['evidence_ids'][0]],x['mechanism_id']))
    return ranked


def recovery_metrics(root, report, *, mock):
    phases = {'analyze':[], 'merge':[], 'generate':[]}
    for name, phase in [('analysis_*','analyze'), ('merge','merge'), ('candidate_*','generate')]:
        for journal in sorted(root.glob(name+'/compiler.jsonl')):
            rows = EvidenceStore(journal).records()
            requests = [r['payload'] for r in rows if r['kind']=='GENERATION_REQUESTED']
            responses = [r['payload']['response'] for r in rows if r['kind']=='GENERATION_RESPONSE']
            for request in requests:
                # No usage is inferred for unfinished calls. The shared ledger
                # separately retains their full reservation.
                result = responses[0] if responses else {}
                phases[phase].append(dict(job=journal.parent.name, request_sha256=fingerprint(request),
                    response_id=result.get('id'), usage=result.get('usage') or {},
                    provider_finish_reason=result.get('finish_reason')))
    counts = {}
    for phase, records in phases.items():
        inputs = sum(r['usage'].get('input_tokens') or 0 for r in records)
        outputs = sum(r['usage'].get('output_tokens') or 0 for r in records)
        metered = sum(type(r['usage'].get('total_tokens')) is int for r in records)
        counts[phase] = dict(calls=len(records), metered_responses=metered, input_tokens=inputs,
                             output_tokens=outputs, cost_scope='MOCK_ZERO_PAID' if mock else 'PEAK_NO_CACHE_ESTIMATE',
                             estimated_usd=0 if mock else (inputs*.30+outputs*1.20)/1_000_000,
                             requests=records)
    workers = [e['payload'] for e in EvidenceStore(root/'worker.jsonl').records()
               if e['kind']=='ENVIRONMENT_POLICY_EXECUTED']
    checks = [check for candidate in report.get('candidates',[]) for check in candidate.get('checks',[])]
    return dict(phases=counts, outcomes={status:sum(c['status']==status for c in checks) for status in
                    ('LOCAL_REPAIR_VERIFIED','EPISODE_WON','PROGRESS_UNVERIFIED','REPAIR_FAILED','DECLINED','POLICY_ERROR')},
                local_repairs=sum(c['local_repair_verified'] for c in checks),
                episode_wins=sum(c['episode_won'] for c in checks),
                registered_shadow=sum(c['status']=='SHADOW' for c in report.get('candidates',[])),
                worker_checks_passed=len({w['candidate_version'] for w in workers
                    if w['result']['status']!='error'}-{w['candidate_version'] for w in workers
                    if w['result']['status']=='error'}),
                source_worker_calls=len(workers), source_worker_seconds=sum(w['seconds'] for w in workers),
                independent_checks=0, independent_passes=0)


def acquire_recoveries(events, host, root, budget, registry, runner, data, **transport):
    if len(events)!=16 or any(e['event_type']!='LOCAL_FAILURE_RECOVERY' or not e['won'] for e in events):
        raise PermissionError('expected frozen recovery cohort')
    if len({e['evidence_id'][:12] for e in events})!=len(events):
        raise PermissionError('step namespace collision')
    stream = budget.config['run_id']
    ids = import_source_events('B',events,host,root,registry.evidence,stream)
    analyses = []
    rejected = []
    for i in range(0,len(events),BATCH_SIZE):
        batch = events[i:i+BATCH_SIZE]
        batch_index = i//BATCH_SIZE
        views = [recovery_view(event,(host[event['evidence_id']]['steps'][event['anchor']-2]
                 if event['anchor']>1 else host[event['evidence_id']]['initial'])['commands']) for event in batch]
        result = stage_request(root,f'analysis_{batch_index}','analyze',dict(events=views),
                               lambda value:parse_step_analyses(value,batch),budget,**transport)
        if result.get('parse_status'):
            rejected.extend(dict(batch=batch_index,evidence_id=e['evidence_id'],reason='BATCH_DELIVERY_REJECTED',
                                 diagnostic=result.get('contract_diagnostic')) for e in batch)
        else:
            batch_receipt = json.loads(result['specification'])
            analyses.extend(batch_receipt['analyses'])
            rejected.extend(dict(r,batch=batch_index) for r in batch_receipt['rejected'])
    save(root/'analyses.json',dict(analyses=analyses,rejected=rejected))
    eligible = [a for a in analyses if a['decision']=='HYPOTHESIS']
    report = dict(evidence=len(events),localized=len(analyses),grounded_hypotheses=len(eligible),
                  abstentions=len(analyses)-len(eligible),rejected_evidence=len(events)-len(analyses),
                  rejection_records=len(rejected),candidates=[])
    if len(eligible)<MIN_GROUNDED_HYPOTHESES:
        status = 'ALL_ABSTAINED' if len(analyses)==len(events) and not eligible else 'INSUFFICIENT_GROUNDED_EVIDENCE'
        return dict(report,status=status,mechanisms=0)
    merged = stage_request(root,'merge','merge',dict(analyses=eligible),
                           lambda value:parse_mechanisms(value,eligible),budget,**transport)
    if merged.get('parse_status'):
        return dict(report,status='MERGE_DELIVERY_REJECTED', reason=merged.get('contract_diagnostic'))
    merged = json.loads(merged['specification'])
    ranked = rank_mechanisms(merged,analyses)
    save(root/'mechanisms.json',dict(ranking=ranked,uncertainty=merged['uncertainty'],rejected=merged['rejected'],
         unassigned=[a['evidence_id'] for a in eligible if not any(
             a['evidence_id'] in x['proposal']['evidence_ids'] for x in ranked)]))
    report['mechanisms'] = len(ranked)
    report['rejected_mechanisms'] = len(merged['rejected'])
    by_id = {a['evidence_id']:a for a in eligible}
    known = {e['event_id']:e for e in registry.evidence.visible(time.time(),stream)}
    for rank,item in enumerate(ranked):
        receipt = dict(item)
        report['candidates'].append(receipt)
        if rank >= MAX_CANDIDATES:
            receipt.update(status='NOT_SELECTED',reason='FROZEN_MECHANISM_CAP')
            continue
        name = 'candidate_'+item['mechanism_id']
        chosen = item['proposal']['evidence_ids']
        payload = dict(mechanism=item['proposal'], analyses=[by_id[eid] for eid in chosen])
        generated = stage_request(root,name,'generate',payload,None,budget,**transport)
        if generated.get('parse_status'):
            receipt.update(status='SOURCE_DELIVERY_REJECTED',reason=generated.get('contract_diagnostic'))
            continue
        code = generated['code']
        if static_check(code)['passed'] and _has_instance_literals(code, [host[eid] for eid in ids]):
            receipt.update(status='INSTANCE_LITERAL_REJECTED')
            continue
        # The entire B cohort influenced the model upstream. Preserve it as
        # provenance; only cited evidence is counted as this mechanism's support.
        receipt.update(register_environment_candidate(root/name,generated,item['proposal'],list(ids.values()),
            known,runner.backend.manifest(),registry,engineering=transport.get('sender') is not None,
            protocol=VERSION,baseline='alfworld-full-library-online'))
        save(root/name/'candidate_receipt.json', receipt)
        if receipt['status']=='SHADOW':
            card = FailureOperator.from_dict(receipt['card'])
            receipt['checks'] = [review_source(data,host[ref['evidence_id']],ref,card,runner,registry,
                root/name/f'review_{i}.json',extended=True) for i,ref in enumerate(item['checkpoints'])]
            if registry.state(card)['permission']!='shadow':
                raise PermissionError('source-only candidate has unexpected permission')
            save(root/name/'candidate_receipt.json', receipt)
    return dict(report,status='SOURCE_ONLY_COMPLETE' if ranked else (
        'MERGE_DELIVERY_REJECTED' if merged['rejected'] else 'NO_MECHANISM'))
