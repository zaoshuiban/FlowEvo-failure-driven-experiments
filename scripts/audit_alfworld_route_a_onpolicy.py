"""P2: read-only native-trajectory opportunity audit and action-free gate Shadow.

Never boot TextWorld, invoke S0, generate a candidate, or change a native trace.
Bridge reachability is a no-intervention replay, not an online effect estimate.
"""
import argparse
from collections import Counter
import fcntl
from pathlib import Path
from types import SimpleNamespace
import time

import audit_alfworld_route_a_semantic_boundaries as M
import run_alfworld_route_a_value_validation as V
from diagnose_alfworld_online_failures import export_episode
from alfworld_.route_b_runtime import RecoveryBridge
from alfworld_.generator import AlfWorldStepOutput
from alfworld_.skill_library import SkillLibrary
from alfworld_.precondition_diagnostic import command,receipt_effect

A=M.A; P=M.P; ROOT=M.ROOT
NATIVE=Path.home()/'.local/share/flowevo/alfworld_full_library_online120_20261109_01'
OUT=ROOT/'runs/alfworld_route_a_onpolicy_opportunity_20261117_01'
MIN_REPAIR_STEPS=2 # lower bound for opening and retry; not guaranteed completion
DECISION_RULE='EVIDENCE_INSUFFICIENT if any native episode cannot be audited or any gate errors; otherwise TRIGGER_COVERAGE_TOO_LOW if no potential opportunity overlaps a native-lost game; otherwise ONLINE_PILOT_WORTHWHILE for a bounded pilot only. This rule addresses success-rate value; cost-only opportunities reported separately, not a safety release.'


def project(ep,index):
    """index is the executed action's 1-based index; suffix is host-only."""
    if not 1<=index<=len(ep['steps']):raise ValueError('anchor')
    prefix=ep['steps'][:index];after=prefix[-1]['feedback']
    required=('action','observation','commands','won','done')
    if (not isinstance(ep.get('goal'),str) or any(k not in after for k in required)
            or any('action' not in s['feedback'] or 'observation' not in s['feedback'] for s in prefix)):
        raise ValueError('NOT_EVALUABLE_MISSING_PUBLIC_CONTEXT')
    return P.context_view(ep['goal'],after['observation'],after['commands'],
        [dict(action=s['feedback']['action'],observation=s['feedback']['observation']) for s in prefix],{})


def mechanism(context):
    parsed=command(context['history'][-1]['action'])
    if parsed and parsed[0]=='move':
        target=parsed[1][1].name;failed=context['history'][-1]['action']
        return ('CLOSED_OPENABLE_DESTINATION_PLACEMENT' if 'open '+target in context['admissible_commands'] and failed not in context['admissible_commands']
                else 'PLACEMENT_OTHER_OR_UNRESOLVED')
    if context['history'][-1]['action'].startswith('go to '):return 'NAVIGATION_NO_EFFECT'
    return 'OTHER_NO_EFFECT'


def bridge_audit(ep):
    """Run the unchanged bridge with an always-declining observer.

    The native stub returns recorded actions, never calls an LLM. No recovery
    is selected; the whole timeline therefore stays the actual native timeline.
    """
    touched=[];next_action=['']
    def native_step(**kw):return AlfWorldStepOutput(action=next_action[0],model_calls=1)
    native=SimpleNamespace(step=native_step)
    def inspect_only(**kw):
        touched.append(len(kw['action_history']))
        return native.step(**kw)
    policy=SimpleNamespace(native=native,states={},used=[],errors=set(),step=inspect_only)
    bridge=RecoveryBridge(policy,episode_limit=50,window=18,max_opportunities=2)
    callbacks=[]
    for s in ep['steps']:
        if s['decision']['source']!='MODEL':continue
        anchor=s['step']-1;callbacks.append(anchor)
        ctx=project(ep,anchor) if anchor else dict(goal=ep['goal'],observation=ep['initial']['observation'],
            admissible_commands=ep['initial']['commands'],history=[])
        next_action[0]=s['feedback']['action']
        result=bridge.step(task_goal=ctx['goal'],observation=ctx['observation'],admissible_commands=ctx['admissible_commands'],
            action_history=[x['action'] for x in ctx['history']],observation_history=[x['observation'] for x in ctx['history']],
            skill_context='',policy_directives=None) # unused guidance; only callback/trigger semantics tested
        if result.action!=next_action[0] or result.model_calls!=1:raise PermissionError('native replay changed')
    return dict(callback_anchors=callbacks,trigger_anchors=touched,opportunities=bridge.opportunities,
        shadow_actions_selected=0,interpretation='COMPONENT_ATTACHED_NO_INTERVENTION_REPLAY_NOT_HISTORICAL_ACTUAL_BRIDGE')


def suffix_outcome(ep,index):
    failed=ep['steps'][index-1]['feedback']['action'];parsed=command(failed)
    success=next((s for s in ep['steps'][index:] if s['feedback']['action']==failed
        and receipt_effect(parsed,s['feedback']['observation'])=='TRUE'),None)
    later=ep['steps'][index:success['step']] if success else []
    return dict(same_action_repair_step=success['step'] if success else None,
        same_action_repair_verified=bool(success),steps_until_same_action_repair=success['step']-index if success else None,
        native_model_calls_until_repair=sum(s['decision']['source']=='MODEL' for s in later) if success else None,
        repair_request_ids=[s['requested']['request_id'] for s in later if s['requested']] if success else [],
        eventual_won=ep['steps'][-1]['feedback']['won'],
        causal_attribution='NOT_ESTABLISHED; later native success is not a candidate benefit')


def require_settled(path):
    rows=P.EvidenceStore(path).records();reserved={};settled=set()
    for e in rows:
        q=e['payload']
        if e['kind']=='RESERVED':
            if q['request_id'] in reserved:raise PermissionError('duplicate reservation')
            reserved[q['request_id']]=q
        if e['kind']=='SETTLED':settled.add(q['request_id'])
        if 'UNKNOWN' in e['kind']:raise P.RunUnhealthy('historical unknown ledger')
    if set(reserved)!=settled:raise P.RunUnhealthy('historical unsettled budget')
    return dict(reserved=len(reserved),settled=len(settled))


def cohort(native=NATIVE):
    protocol=A.read(native/'protocol.json');summary=A.read(native/'summary.json')
    commits=P.EvidenceStore(native/'episodes.jsonl').records();entries=[x['payload'] for x in commits]
    if len(entries)!=120 or any(x['kind']!='EPISODE_COMMITTED' for x in commits):raise PermissionError('expected native120 commits')
    if protocol['condition']!='full_library' or not protocol['online']:raise PermissionError('wrong baseline')
    if summary['status']!='COMPLETED' or summary['protocol_sha256']!=A.digest(protocol):raise PermissionError('baseline not complete')
    ledger=require_settled(native/'budget.jsonl')
    tasks={x['task_id']:x for x in protocol['tasks']};previous=SkillLibrary().to_dict();episodes=[];rows=[];unverified=[]
    for seq,(e,event) in enumerate(zip(entries,commits),1):
        if e['seq']!=seq or e['before']!=A.digest(previous) or e['protocol_sha256']!=A.digest(protocol):raise PermissionError('chronology/bank binding')
        epdir=native/'episodes'/e['task_id'];locked=A.read(epdir/'locked.json')
        if locked!=e['outcome']:raise PermissionError('locked result differs')
        if e['library_sha256']!=A.digest(e['library']):raise PermissionError('bank changed')
        try:
            ep=export_episode(native,e,previous) # only public export, never retrospective probes
            if ep['initial']['game']!=str(Path(protocol['data_root'])/tasks[e['task_id']]['game']):raise ValueError('game identity')
            if ep['goal']!=ep['initial']['observation'].split('Your task is to:')[-1].strip():
                # Native helper is case insensitive; do not fabricate a goal.
                from alfworld_.env import _goal_from_observation
                if ep['goal']!=_goal_from_observation(ep['initial']['observation']):raise ValueError('goal/observation mismatch')
            if bool(ep['steps'][-1]['feedback']['won'])!=e['outcome']['trace']['success']:raise ValueError('won/trace mismatch')
            bridge=bridge_audit(ep);bad=[]
            for s in ep['steps']:
                if 'nothing happens' not in s['feedback']['observation'].lower():continue
                i=s['step'];ctx=project(ep,i);after=s['feedback'];callback=i in bridge['callback_anchors'];reached=i in bridge['trigger_anchors']
                why=('OBSERVABLE_WITH_CURRENT_BRIDGE_COMPONENT' if reached else
                     'L1_INTERNAL_FEEDBACK_SUPERSEDED' if i<ep['direct_prefix'] else
                     'TERMINAL_ENVIRONMENT_OR_BUDGET' if after['done'] or i>=50 else
                     'NO_NEXT_NATIVE_GENERATOR_CALL' if not callback else 'TRIGGER_CAP_OR_RECEIPT_RULE')
                raw=dict(event_id=e['task_id']+f'/step_{i:03}',task_id=e['task_id'],sequence=seq,step=i,
                    source_type='NATURAL_NATIVE_FULL_LIBRARY',game_sha256=tasks[e['task_id']]['game_sha256'],
                    task_group=tasks[e['task_id']]['group'],scene=tasks[e['task_id']]['scene'],task_type=ep['task_type'],
                    physical_checkpoint_id=A.digest([tasks[e['task_id']]['game_sha256'],[x['feedback']['action'] for x in ep['steps'][:i]]]),
                    receipt_sha256=s['receipt_sha256'],commit_record_sha256=event['record_hash'],
                    source_environment=str(epdir/'environment.jsonl'),source_sha256=A.sha(epdir/'environment.jsonl'),
                    producer=s['decision']['source'],l1_executed=s['decision']['l1_executed'],l2_injected=s['decision']['l2_injected'],l3_injected=s['decision']['l3_injected'],
                    next_native_guidance=ep['steps'][i]['decision'] if callback else None,
                    bridge_callback=callback,bridge_visible=reached,bridge_reason=why,
                    context=ctx,context_status='AUDITABLE',mechanism=mechanism(ctx),remaining_steps=50-i,
                    remaining_window=min(18,50-i),original_action_legal=s['action_was_legal'],
                    native_suffix=suffix_outcome(ep,i),shadow_only=True)
                rows.append(raw);bad.append(raw['event_id'])
            episodes.append(dict(sequence=seq,task_id=e['task_id'],task_type=ep['task_type'],scene=tasks[e['task_id']]['scene'],
                task_group=tasks[e['task_id']]['group'],status='AUDITABLE',won=e['outcome']['trace']['success'],
                steps=len(ep['steps']),L1_actions=ep['direct_prefix'],model_calls=e['outcome']['trace']['llm_call_count'],
                l2_requests=e['outcome']['use']['L2_requests'],l3_requests=e['outcome']['use']['L3_requests'],
                no_effect_events=bad,bridge=bridge))
        except (AssertionError,ValueError,KeyError,TypeError) as exc:
            # Missing records are explicitly not equivalent to zero opportunity.
            rows=[x for x in rows if x['task_id']!=e['task_id']]
            unverified.append(dict(sequence=seq,task_id=e['task_id'],status='NOT_EVALUABLE',reason=type(exc).__name__+':'+str(exc)))
        previous=e['library']
    final=A.read(native/'final_bank.json')
    if final['seq']!=120 or final['library']!=previous or final['committed_payload_sha256']!=A.digest(entries[-1]):raise PermissionError('final bank binding')
    drift=[f for f,h in protocol['source_sha256'].items() if not Path(f).exists() or A.sha(f)!=h]
    for name in ('executor.py','generator.py'):
        if any(Path(f).name==name for f in drift):raise PermissionError('historical action-path implementation changed')
    return dict(episodes=episodes,failures=rows,not_evaluable=unverified,ledger=ledger,
        original_source_drift=drift,original_protocol_sha256=A.digest(protocol),historical_summary=summary)


def prepare(out=OUT):
    if (out/'protocol.json').exists():return verify(out)
    M.verify();bundle=cohort();parent=A.read(M.PHASE/'protocol.json')
    import alfworld_.route_b_runtime as bridge
    import alfworld_.learning_runtime as runtime
    import alfworld_.executor as executor
    import alfworld_.success_baseline as baseline
    import diagnose_alfworld_online_failures as exporter
    code=[Path(__file__).resolve(),ROOT/'scripts/test_alfworld_route_a_onpolicy.py',
        *[Path(x.__file__).resolve() for x in (bridge,runtime,executor,baseline,exporter)]]
    history={str(f):A.sha(f) for f in NATIVE.rglob('*') if f.is_file() and f.suffix not in ('.lock','.pyc')}
    history.update({str(f):A.sha(f) for f in code})
    history.update(parent['files'])
    online=A.read(M.C.V.N.OLD/'online/selection.private.json')['tasks']
    native_groups={x['task_group'] for x in bundle['episodes']}
    if native_groups & {x['task']['group'] for x in online}:raise PermissionError('reserved online overlap')
    out.mkdir(parents=True,exist_ok=True)
    A.commit(out/'contexts.private.json',bundle)
    p=dict(version='route-a-p2-onpolicy-v1',run_id=out.name,files=history,
        input_sha256=A.sha(out/'contexts.private.json'),worker=parent['worker'],
        candidates=parent['candidates'],joint_sha256=parent['joint_sha256'],candidate_version=parent['candidate_version'],
        max_calls=0,max_tokens=0,max_cost_microusd=0,worker_calls=len(bundle['failures']),environment_steps=0,
        episode_limit=50,source_window=18,max_opportunities=2,min_repair_steps=MIN_REPAIR_STEPS,
        native_path=str(NATIVE),historical_actual_bridge_enabled=False,
        bridge_scope='Replay current RecoveryBridge at verified native model callbacks; observer always declines so native actions are unchanged; guidance fields unused by trigger',
        gate_scope='All auditable natural no-effect states, including offline-only unreachable states; primary funnel only bridge-visible container states',
        remaining_steps_interpretation='2 is a necessary open+retry lower bound, not a completion guarantee;18 is a cap not a minimum',
        decision_rule=DECISION_RULE,permission='SHADOW',recovery_execution_allowed=False,online_authorized=False,
        score_boundary='Opportunity and native later recovery only; no candidate repair or counterfactual gain measured')
    return A.commit(out/'protocol.json',p)


def verify(out=OUT):
    M.verify();p=A.read(out/'protocol.json');P.verify_history(p['files'])
    if p['input_sha256']!=A.sha(out/'contexts.private.json') or p['max_calls'] or p['max_cost_microusd'] or p['environment_steps'] or p['online_authorized'] or p['recovery_execution_allowed']:
        raise PermissionError('P2 scope or input drift')
    if p['candidates']['Route_A']['sha256']!=M.EXPECTED_GATE or p['candidates']['S0']['sha256']!=M.EXPECTED_RECOVERY:raise PermissionError('candidate drift')
    return p


def evaluate(out=OUT):
    p=verify(out);bundle=A.read(out/'contexts.private.json')
    with (out/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget,runner,registry,receipts,recovery,gate=V.setup(out,p)
        if (out/'result.json').exists():return A.read(out/'result.json')
        done=[]
        for item in bundle['failures']:
            # Only the gate artifact is sent to Worker. S0 is never invoked.
            decision=V.B.learned_decision(runner,gate,item['context'])
            receipt=next(e['payload'] for e in runner.events.records() if e['kind']=='ENVIRONMENT_POLICY_EXECUTED' and e['payload']['execution_id']==decision['execution_id'])
            if receipt['artifact_sha256']!=gate.artifact_sha256 or receipt['result']['status']!='declined':raise PermissionError('not an action-free gate')
            done.append(dict(event_id=item['event_id'],context_sha256=A.digest(item['context']),
                decision=decision,worker_artifact_sha256=gate.artifact_sha256,original_candidate_version=p['candidate_version']))
        if any(registry.state(c)['permission']!='shadow' or not c.intact() for c in (gate,recovery)):raise PermissionError('permission boundary')
        if receipts.started:raise PermissionError('environment executed in Shadow audit')
        P.check_run(budget,SimpleNamespace(events=P.EvidenceStore(out/'provider.jsonl')),runner)
        verify(out)
        return A.commit(out/'result.json',dict(status='P2_GATE_SHADOW_COMPLETED',rows=done,budget=budget.snapshot(),
            model_calls=0,environment_steps=0,recovery_actions=0,online_executed=False,permission='SHADOW'))


def count(rows):return dict(events=len(rows),games=len({r['task_id'] for r in rows}))


def summarize(bundle,decisions):
    lookup={r['event_id']:r['decision'] for r in decisions};rows=[]
    for item in bundle['failures']:
        r=dict(item);r['gate']=lookup.get(r['event_id'],dict(status='NOT_EVALUABLE',reason='MISSING_GATE_RECEIPT'))
        r['potential']=r['bridge_visible'] and r['mechanism']=='CLOSED_OPENABLE_DESTINATION_PLACEMENT' and r['gate']['status']=='MATCH' and r['remaining_steps']>=MIN_REPAIR_STEPS
        rows.append(r)
    visible=[r for r in rows if r['bridge_visible']]
    container=[r for r in visible if r['mechanism']=='CLOSED_OPENABLE_DESTINATION_PLACEMENT']
    available=[r for r in container if r['context_status']=='AUDITABLE']
    matched=[r for r in available if r['gate']['status']=='MATCH'];potential=[r for r in matched if r['potential']]
    not_evaluable=bundle['not_evaluable'];errors=[r for r in rows if r['gate']['status'] in ('ERROR','NOT_EVALUABLE')]
    lost=[r for r in potential if not r['native_suffix']['eventual_won']]
    verdict='EVIDENCE_INSUFFICIENT' if not_evaluable or errors else 'ONLINE_PILOT_WORTHWHILE' if lost else 'TRIGGER_COVERAGE_TOO_LOW'
    return rows,dict(recommendation=verdict,decision_rule=DECISION_RULE,
        interpretation='Success-rate investment decision; nonzero cost-saving opportunities do not imply observed net savings or absence of opportunities.',
        evaluated_native_games=len(bundle['episodes']),native_successes=sum(e['won'] for e in bundle['episodes']),native_steps=sum(e['steps'] for e in bundle['episodes']),
        native_model_calls=sum(e['model_calls'] for e in bundle['episodes']),
        funnel=[dict(stage=n,**count(v)) for n,v in zip(('NATIVE_NO_EFFECT','BRIDGE_OBSERVABLE','CONTAINER_MECHANISM','PUBLIC_CONTEXT_AUDITABLE','GATE_MATCH','ENOUGH_REMAINING_STEPS'),(rows,visible,container,available,matched,potential))],
        all_container_failures=count([r for r in rows if r['mechanism']=='CLOSED_OPENABLE_DESTINATION_PLACEMENT']),
        gate_all=dict(Counter(r['gate']['status'] for r in rows)),gate_container=dict(Counter(r['gate']['status'] for r in container)),
        bridge_exclusions={reason:count([r for r in rows if not r['bridge_visible'] and r['bridge_reason']==reason]) for reason in sorted({r['bridge_reason'] for r in rows if not r['bridge_visible']})},
        by_mechanism={m:count([r for r in rows if r['mechanism']==m]) for m in sorted({r['mechanism'] for r in rows})},
        source_layers={k:count([r for r in rows if r[k]]) for k in ('l1_executed','l2_injected','l3_injected')},
        next_callback_guidance={k:count([r for r in visible if r['next_native_guidance'] and r['next_native_guidance'][k]]) for k in ('l2_injected','l3_injected')},
        native_self_repair_potential=count([r for r in potential if r['native_suffix']['same_action_repair_verified']]),
        potential_native_lost=count(lost),potential_native_won=count([r for r in potential if r['native_suffix']['eventual_won']]),
        natural_failures_in_lost_games=count([r for r in rows if not r['native_suffix']['eventual_won']]),
        native_failed_games=[e['task_id'] for e in bundle['episodes'] if not e['won']],
        no_noeffect_games=sum(not e['no_effect_events'] for e in bundle['episodes']),
        no_container_failure_games=len(bundle['episodes'])-len({r['task_id'] for r in rows if r['mechanism']=='CLOSED_OPENABLE_DESTINATION_PLACEMENT'}),
        native_repair_steps=dict(Counter(str(r['native_suffix']['steps_until_same_action_repair']) for r in potential)),
        native_repair_model_calls=sum(r['native_suffix']['native_model_calls_until_repair'] or 0 for r in potential),
        uncertain_binding=count([r for r in container if r['gate']['status']=='UNKNOWN']),
        insufficient_remaining=count([r for r in matched if not r['potential']]),not_evaluable=not_evaluable,errors=count(errors),
        permission='SHADOW',safety_readiness='ORIGINAL_CONFIRMATION_NO_GO_UNCHANGED',online_executed=False,
        candidate_repair_success='NOT_EVALUATED',native_counterfactual_gain='NOT_EVALUATED')


def analyze(out=OUT):
    p=verify(out);bundle=A.read(out/'contexts.private.json');result=A.read(out/'result.json')
    if {r['event_id'] for r in result['rows']}!={r['event_id'] for r in bundle['failures']}:raise PermissionError('incomplete output')
    rows,summary=summarize(bundle,result['rows'])
    w=P.EvidenceStore(out/'worker.jsonl').records();executed=[x['payload'] for x in w if x['kind']=='ENVIRONMENT_POLICY_EXECUTED']
    started=[x['payload']['execution_id'] for x in w if x['kind']=='ENVIRONMENT_POLICY_STARTED']
    if sorted(started)!=sorted(x['execution_id'] for x in executed) or len(started)!=len(set(started)):raise P.RunUnhealthy('pending/duplicate Worker')
    for x in result['rows']:
        r=next(y for y in rows if y['event_id']==x['event_id']);raw=next(y for y in executed if y['execution_id']==x['decision']['execution_id'])
        if raw['context_sha256']!=A.digest(r['context']) or raw['artifact_sha256']!=x['worker_artifact_sha256']:raise PermissionError('Worker/context binding')
    summary.update(protocol_sha256=A.digest(p),candidate_sha256=M.EXPECTED_GATE,recovery_sha256=M.EXPECTED_RECOVERY,
        worker_calls=len(executed),worker_seconds=sum(x['seconds'] for x in executed),new_api_usd=0,new_model_calls=0,new_environment_steps=0,
        source_protocol_sha256=bundle['original_protocol_sha256'],historical_native_cost_reference_usd=bundle['historical_summary']['total_reference_offpeak_usd'],
        native_ledger=bundle['ledger'],source_drift=bundle['original_source_drift'])
    A.commit(out/'Detailed_Audit.private.json',dict(rows=rows,episodes=bundle['episodes'],summary=summary))
    public=ROOT/'reports/alfworld_route_a_onpolicy_opportunity_20261117';public.mkdir(parents=True,exist_ok=True)
    # IDs, denominators and reasons are public; full goals/history/request content stay local.
    summary['event_records']=[{k:v for k,v in r.items() if k not in ('context','next_native_guidance','source_environment')} for r in rows]
    summary['episodes']=bundle['episodes']
    A.commit(public/'public_audit_summary.json',summary)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','evaluate','analyze']);parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();v=globals()[args.command](args.output.resolve());print(v.get('recommendation',v.get('status',A.digest(v))))
