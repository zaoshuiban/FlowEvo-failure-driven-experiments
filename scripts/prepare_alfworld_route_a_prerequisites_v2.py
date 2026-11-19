"""One bounded MODEL gate revision, then new independent confirmation.

Preparation never sends a request or resets a new game. Historical gates,
recovery, labels and online roster are immutable. No host-written gate.
"""
import argparse
import fcntl
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import run_alfworld_route_a_value_validation as V
from alfworld_.recovery_applicability_learning import REVISION_PROMPT
from alfworld_.python_recovery_feedback import parse_delivery, delivery
from alfworld_.recovery_acquisition import stage_request

A=V.A; P=V.P; B=V.B; X=V.X; ROOT=V.ROOT
OLD=ROOT/'runs/alfworld_route_a_online_value_20261117_01'
VERSION='route-a-processing-prerequisites-v2'
SEED='ROUTE_A_PREREQUISITES_V2_20261117'
PROMPT=REVISION_PROMPT+'''
This is one gate-only development revision of an archived candidate, not a new
recovery algorithm. Its prior independent checks are now exposed development
evidence. Preserve supported simple placement. Derive required processing from
the actual goal, including adjective forms, and demand successful public receipts
for the same object instance. A legal open/move command, an attempted processing
action, or a candidate explanation is not proof of processing. Distinguish missing
evidence, contradictory evidence, final delivery and preparatory actions. Reject
ambiguous instance bindings. Do not invent a negative label merely because an
episode has not won. Do not assume undisclosed history is complete. You may abstain.
Keep the gate compact enough for the frozen 4096-output-token delivery limit.
Return complete source, never a patch. reason in every gate return is <=400 chars.
No evaluation reference routes, hidden state, independent games, Rule or new
online task information are supplied. No further model revision is permitted.
'''
POLICY=dict(version='route-a3-wire-v1',model='deepseek-flash',max_wire_input_bytes=100000,
    max_input_tokens=100256,model_context_tokens=131072,output_tokens=4096,
    estimator='UTF8_BYTES_PLUS_256_UPPER')


def public_feedback(sample,row):
    """Only an actual public view and reviewed development label, no probes."""
    ctx=sample['candidate_context']
    if set(ctx)!={'goal','observation','admissible_commands','history'}:
        raise PermissionError('public context whitelist')
    if any(set(step)!={'action','observation'} for step in ctx['history']):
        raise PermissionError('history whitelist')
    return dict(evidence_id=A.digest(sample['sample_id']),public_context=ctx,
        public_history_scope=sample.get('public_history_scope',{}),
        supervision=dict(label=sample['label'],rationale=sample['reason'],
                         status=sample['label_status'],origin='EXPOSED_DEVELOPMENT_REVIEW'),
        candidate_self_report=dict(status=row['decision']['status'],reason=row['decision'].get('reason',''),
                                   trust='CANDIDATE_CLAIM_NOT_ENVIRONMENT_FACT'))


def feedback_packet():
    samples=A.read(OLD/'checkpoints.private.json')['samples']
    rows={r['sample_id']:r for r in A.read(OLD/'result.json')['rows']}
    # All observed unsafe cases, then first two per task-type/label in frozen
    # checkpoint order. No selection from the new independent pool.
    chosen=[];counts=Counter()
    for s in samples:
        row=rows[s['sample_id']]
        if row['score']['unsupported_recovery'] or row['score']['false_final_delivery_recovery']:
            chosen.append(s)
    for s in samples:
        key=(s['task_type'],s['label'])
        if counts[key]<2:
            counts[key]+=1
            if s not in chosen:chosen.append(s)
    parent=A.read(OLD/'protocol.json')['candidates']
    packet=dict(parent_gate_sha256=parent['Route_A']['sha256'],
        previous_code=Path(parent['Route_A']['path']).read_text(),
        recovery_sha256=parent['S0']['sha256'],recovery_code=Path(parent['S0']['path']).read_text(),
        feedback=[public_feedback(s,rows[s['sample_id']]) for s in chosen],
        scope='DEVELOPMENT_ONLY_NO_INDEPENDENT_RESULTS',
        diagnostics=['Processing adjective removed for object binding can be lost as a prerequisite.',
                     'Preserve verified simple-placement opportunities while handling required processing.'])
    return packet,[s['sample_id'] for s in chosen]


def select(audit):
    rows=[r for r in audit['eligible'] if r['task']['split']=='train'
          and r['task']['task_type'] in V.TYPES and r['task']['group'].rsplit('-',2)[-2] in V.TARGETS]
    counts=[Counter(),Counter(),Counter()];chosen=[];groups=set()
    def features(r):
        t=r['task'];return t['task_type'],t['group'].rsplit('-',2)[-2],t['scene']
    while len(chosen)<48:
        remaining=[r for r in rows if r['task']['group'] not in groups]
        if not remaining:raise PermissionError('insufficient new task groups; never borrow online games')
        row=min(remaining,key=lambda r:tuple(c[v] for c,v in zip(counts,features(r)))+(A.digest([SEED,r['task']['game_sha256']]),))
        chosen.append(dict(row,role='V2_INDEPENDENT_CONFIRMATION'));groups.add(row['task']['group'])
        for c,v in zip(counts,features(row)):c[v]+=1
    return chosen


def prepare(root):
    if (root/'generation/protocol.json').exists():return verify_preparation(root)
    audit=A.read(root/'exposure.private.json')
    if audit['malformed']:raise PermissionError('exposure audit incomplete')
    parent=A.read(OLD/'protocol.json');P.verify_history(parent['files'])
    packet,ids=feedback_packet();selected=select(audit)
    online=A.read(OLD/'online/selection.private.json')
    if {r['task']['group'] for r in selected}&{r['task']['group'] for r in online['tasks']}:
        raise PermissionError('online isolation')
    A.commit(root/'confirmation_selection.private.json',dict(tasks=selected,seed=SEED,replacement_allowed=False))
    A.commit(root/'generation/input.private.json',packet)
    wire=B.wire(root/'generation',packet,PROMPT,0,POLICY)
    files={str(p):A.sha(p) for p in (Path(__file__).resolve(),ROOT/'scripts/test_alfworld_route_a_prerequisites_v2.py',
        OLD/'protocol.json',OLD/'checkpoints.private.json',OLD/'result.json',
        OLD/'online/selection.private.json',OLD/'online/Method_Freeze.json')}
    files.update({x['path']:x['sha256'] for x in parent['candidates'].values()})
    files.update({str(Path(m.__file__).resolve()):A.sha(m.__file__) for m in list(sys.modules.values())
        if getattr(m,'__file__',None) and str(m.__file__).endswith('.py') and Path(m.__file__).resolve().is_relative_to(ROOT)})
    runtime=ROOT/'scripts/run_alfworld_route_a_prerequisites_v2.py'
    files[str(runtime)]=A.sha(runtime)
    for module in (V,X,B):files[str(Path(module.__file__).resolve())]=A.sha(module.__file__)
    plan=dict(version=VERSION,run_id=root.name+'-generation',model='deepseek-flash',temperature=0,
        max_calls=1,max_tokens=POLICY['max_input_tokens']+4096,max_cost_microusd=1000000,worker_calls=0,
        input_policy=POLICY,input_sha256=A.sha(root/'generation/input.private.json'),wire_sha256=A.digest(wire),
        prompt_sha256=A.digest(PROMPT),source_files=files,development_evidence_ids=ids,
        parent_candidate=parent['candidates']['Route_A'],frozen_recovery=parent['candidates']['S0'],
        independent_selection_sha256=A.sha(root/'confirmation_selection.private.json'),
        exposure_sha256=A.sha(root/'exposure.private.json'),online_selection_sha256=A.sha(OLD/'online/selection.private.json'),
        scope='ONE_MODEL_GATE_REVISION_THEN_FROZEN_DEVELOPMENT_AND_INDEPENDENT_VALIDATION',
        paid_authorization_status='PENDING_NEW_EXPLICIT_AUTHORIZATION',online_authorized=False,
        development_rule='All 61 exposed checkpoints; no lost successful positive, no unsafe or ERROR; engineering morphology cases separately.',
        confirmation_rule='All previous capability/coverage/safety thresholds PLUS explicit phase/instance coverage reported; missing trustworthy controls blocks online.',
        request_failure='Keep original response/UNKNOWN/reserve; no auto retry or replacement',
        estimated_reservation_upper_usd=(POLICY['max_input_tokens']+4096)*1.2/1000000,
        cost_note='Existing conservative ledger reservation, not current provider quote or authorization')
    A.commit(root/'generation/wire.private.json',wire);A.commit(root/'generation/protocol.json',plan)
    A.commit(root/'Preparation.json',dict(status='PREPARED_PENDING_MODEL_AUTHORIZATION',
        protocol_sha256=A.digest(plan),confirmation_games=len(selected),
        types=dict(Counter(r['task']['task_type'] for r in selected)),
        scenes=len({r['task']['scene'] for r in selected}),
        new_game_executions=0,paid_requests=0,online_roster_unchanged=True))
    return plan


def verify_preparation(root):
    p=A.read(root/'generation/protocol.json');P.verify_history(p['source_files'])
    if p['version']!=VERSION or p['max_calls']!=1 or p['max_cost_microusd']!=1000000 or p['online_authorized']:
        raise PermissionError('scope drift')
    for path,key in [('generation/input.private.json','input_sha256'),('exposure.private.json','exposure_sha256'),
                     ('confirmation_selection.private.json','independent_selection_sha256')]:
        if A.sha(root/path)!=p[key]:raise PermissionError('freeze drift')
    if A.sha(OLD/'online/selection.private.json')!=p['online_selection_sha256']:raise PermissionError('online roster drift')
    if A.digest(PROMPT)!=p['prompt_sha256']:raise PermissionError('prompt drift')
    wire=B.wire(root/'generation',A.read(root/'generation/input.private.json'),PROMPT,0,POLICY)
    if A.digest(wire)!=p['wire_sha256']:raise PermissionError('actual request drift')
    return p


def required_authorization(p):
    return dict(run_id=p['run_id'],protocol_hash=A.digest(p),model=p['model'],
        protocol=VERSION+':'+A.digest(p),max_cost_microusd=p['max_cost_microusd'],paid_api_authorized=True)


def generate(root,authorization=None,sender=None):
    p=verify_preparation(root)
    if sender is None and authorization!=required_authorization(p):
        raise PermissionError('NEW_EXPLICIT_GATE_REVISION_AUTHORIZATION_REQUIRED')
    out=root/'generation'
    with (out/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget=B.create_accounts(out,p)
        P.check_run(budget,SimpleNamespace(events=P.EvidenceStore(out/'provider.jsonl')),
                    SimpleNamespace(events=P.EvidenceStore(out/'worker.jsonl')))
        if (out/'result.json').exists():return A.read(out/'result.json')
        response=stage_request(out,'revision','analyze',A.read(out/'input.private.json'),parse_delivery,budget,
            sender=sender,authorization=authorization,protocol=VERSION+':'+A.digest(p),
            analysis_prompt=PROMPT,temperature=0,input_policy=POLICY)
        parsed=delivery(response);code=parsed.get('submitted_code') or (parsed.get('proposal') or {}).get('code')
        result=dict(status=parsed['status'],delivery=parsed,origin='MOCK_ENGINEERING_ONLY' if sender else 'REAL_MODEL',
            request_id=response['id'],response_sha256=response['response_sha256'],parent_sha256=p['parent_candidate']['sha256'],
            recovery_sha256=p['frozen_recovery']['sha256'],budget=budget.snapshot(),published=False)
        if code:
            path=out/'candidate.py'
            result['code_sha256']=P.save_exact_source(path,code)
            result['candidate_version']=A.digest([result['code_sha256'],result['parent_sha256'],result['recovery_sha256'],A.digest(p)])
            if parsed['status']=='PROPOSE':
                try:result['static']=P.static_check_detailed(B.worker_artifact(code))
                except (ValueError,SyntaxError,RecursionError) as exc:result['static']=dict(passed=False,error=str(exc))
                result['status']='STATIC_PASSED_PENDING_DEVELOPMENT' if result['static']['passed'] else 'STATIC_REJECTED'
        return A.commit(out/'result.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify_preparation','generate'])
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--authorization',type=Path)
    args=parser.parse_args()
    result=generate(args.output,A.read(args.authorization) if args.authorization else None) if args.command=='generate' else globals()[args.command](args.output)
    print(A.digest(result))
