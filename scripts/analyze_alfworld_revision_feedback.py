"""Summarize the bounded ALFWorld revision run after execution has stopped.

Standard-library artifact reader only: no model, environment, Worker, or runner
imports. Missing evaluations are untested, never invented losses or native wins.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'runs/alfworld_skill_revision_feedback_20261118_01'
REPORT = ROOT/'reports/alfworld_skill_revision_feedback_20261118_01'


def read(path): return json.loads(Path(path).read_text())
def optional(path): return read(path) if path.exists() else None
def canonical(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def commit(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n'
    try:
        with path.open('x') as out:
            out.write(text); out.flush(); os.fsync(out.fileno())
    except FileExistsError:
        if path.read_text() != text: raise PermissionError('immutable result differs: '+str(path))


def journal(path):
    if not path.exists(): return []
    content = path.read_bytes()
    if content and not content.endswith(b'\n'): raise ValueError('partial journal: '+str(path))
    rows = []; previous = '0'*64
    for line in content.splitlines():
        row = json.loads(line)
        if row['previous_hash'] != previous or digest({k:v for k,v in row.items() if k != 'record_hash'}) != row['record_hash']:
            raise ValueError('journal integrity failure: '+str(path))
        previous = row['record_hash']; rows.append(row)
    return rows


def group_of(text):
    if 'SUMMARY' in text: return 'SUMMARY'
    if 'TRACE' in text: return 'TRACE'
    if 'legacy_' in text: return 'LEGACY_DIAGNOSTIC'
    return 'OTHER'


def budget_account(root):
    rows = journal(root/'budget.jsonl'); requests = {}
    if not rows: return dict(present=False, requests={}, totals={}, by_group={}, unknown_or_pending=[])
    for row in rows:
        kind, p = row['kind'], row['payload']; ident = p.get('request_id')
        if kind == 'RESERVED': requests[ident] = dict(p, status='reserved')
        elif kind == 'SETTLED': requests[ident].update(status='settled', settlement=p)
        elif kind == 'UNKNOWN': requests[ident]['status'] = 'unknown'
        elif kind == 'NETWORK_SEND_STARTED': requests[ident]['sent'] = True
        elif kind == 'NOT_SENT': requests[ident]['status'] = 'not_sent'
        elif kind == 'NOT_SENT_REOPENED': requests[ident]['status'] = 'reserved'
    totals = Counter(); groups = defaultdict(Counter)
    for ident, p in requests.items():
        values = Counter()
        values['actual_model_sends'] = int(p['kind'] == 'model' and p.get('sent', False))
        values['not_sent_requests'] = int(p['status'] == 'not_sent')
        if p['status'] != 'not_sent':
            settled = p.get('settlement', {})
            values['model_reservations'] = int(p['kind'] == 'model')
            values['worker_calls'] = int(p['kind'] == 'tool')
            values['charged_or_reserved_tokens'] = settled.get('tokens', p['token_upper'])
            values['conservative_cost_microusd'] = settled.get('cost_microusd', p['cost_upper_microusd'])
            values['worker_milliseconds_charged_or_reserved'] = settled.get('tool_milliseconds', p['tool_milliseconds_upper'])
            values['unknown_or_pending'] = int(p['status'] != 'settled')
        totals.update(values); groups[group_of(p.get('job_id', ident))].update(values)
    return dict(present=True, requests=requests, totals=dict(totals),
        by_group={g:dict(v) for g,v in groups.items()}, config=rows[0]['payload']['config'],
        unknown_or_pending=[dict(request_id=k, kind=v['kind'], job_id=v['job_id'], status=v['status'], sent=v.get('sent', False))
                            for k,v in requests.items() if v['status'] not in ('settled','not_sent')],
        money_note='Conservative retained reservation, not actual supplier billing.', actual_billed_usd=None)


def provider_usage(raw):
    u = raw.get('usage', {}); i = u.get('input_tokens', u.get('prompt_tokens'))
    o = u.get('output_tokens', u.get('completion_tokens')); total = u.get('total_tokens')
    if all(type(x) is int and x >= 0 for x in (i,o,total)) and i+o == total:
        return dict(input_tokens=i, output_tokens=o, total_tokens=total)
    return None


def model_account(root, account):
    rows = []; totals = Counter(); groups = defaultdict(Counter); seen = set()
    for path in sorted((root/'logical_slots').rglob('*.json')):
        slot = read(path); ident = slot['ident']; group = ident.split('/')[1]
        directory = root/'requests'/ident; raw = optional(directory/'response.json')
        wire = read(directory/'request.private.json')
        if digest(wire) != slot['wire_sha256']: raise ValueError('logical request wire mismatch')
        state = account['requests'].get(ident, {}); cached = (directory/'cache.json').exists()
        counted = Counter(logical_requests=1, cache_hits=int(cached), actual_sends=int(state.get('sent', False)))
        u = provider_usage(raw) if raw else None
        if raw and not cached:
            rid = raw.get('id')
            if rid and rid in seen: raise ValueError('duplicate new paid response ID')
            if rid: seen.add(rid)
            counted['received_responses'] += 1
            if u: counted.update(u)
            else: counted['responses_without_trusted_usage'] += 1
        reserve = state.get('settlement', {}).get('cost_microusd', state.get('cost_upper_microusd', 0)) if state.get('status') != 'not_sent' else 0
        counted['conservative_cost_microusd'] += reserve
        groups[group].update(counted); totals.update(counted)
        rows.append(dict(ident=ident, version=group+'_'+ident.split('/')[-1], group=group,
            logical_requests=1, cached=cached, actual_send=bool(state.get('sent')), response_received=raw is not None,
            usage=u, conservative_cost_microusd=reserve, actual_billed_usd=None,
            ledger_status=state.get('status'), request_path=str(directory/'request.private.json'),
            response_path=str(directory/'response.json') if raw else None))
    rejections = []
    for path in sorted((root/'requests').rglob('Input_Size.json')):
        size = read(path)
        if size['passed']: continue
        ident = str(path.parent.relative_to(root/'requests')); parts = ident.split('/')
        rejections.append(dict(ident=ident, group=parts[1], requested_round=parts[-1],
            input_bytes=size['bytes'], frozen_limit_bytes=size['limit'],
            logical_slot_created=(root/'logical_slots'/parts[1]/(parts[-1]+'.json')).exists(),
            actual_send=bool(account['requests'].get(ident, {}).get('sent',False)),
            response_received=(path.parent/'response.json').exists(),
            not_a_model_or_strategy_evaluation=True, evidence_path=str(path)))
    return dict(rows=rows, totals=dict(totals), by_group={g:dict(v) for g,v in groups.items()},
        pre_send_input_rejections=rejections,
        semantics='Only new revision slots are counted. Legacy raw-response copies and reused v0 feedback are not new model requests; cache hits still consume logical slots.')


def environment_account(root):
    events = journal(root/'environment_actions.jsonl'); started = {}; returned = {}; errors = {}; resets = []
    for row in events:
        p = row['payload']
        if row['kind'] == 'ENV_RESET': resets.append(p); continue
        if row['kind'] == 'ENV_ACTION_STARTED':
            if p['number'] in started: raise ValueError('duplicate environment attempt number')
            started[p['number']] = p
        elif row['kind'] == 'ENV_ACTION_RETURNED': returned[p['number']] = p
        elif row['kind'] == 'ENV_ACTION_ERROR': errors[p['number']] = p
    groups = defaultdict(Counter); branches = defaultdict(Counter)
    for number, p in started.items():
        count = Counter(started_actions=1)
        count[p['phase']+'_started_actions'] += 1
        count['returned_actions'] += number in returned
        count[p['phase']+'_returned_actions'] += number in returned
        count['failed_actions'] += number in errors
        count['unknown_actions'] += number not in returned and number not in errors
        groups[group_of(p['branch'])].update(count); branches[p['branch']].update(count)
    for p in resets:
        groups[group_of(p['branch'])]['recorded_resets'] += 1
        branches[p['branch']]['recorded_resets'] += 1
    total = Counter()
    for value in groups.values(): total.update(value)
    return dict(totals=dict(total), by_group={g:dict(v) for g,v in groups.items()},
        by_branch={g:dict(v) for g,v in branches.items()},
        actual_unique_games=sorted({p['game'] for p in resets if p.get('game')}),
        actual_development_unique_games=sorted({p['game'] for p in resets if p.get('game') and p['branch'].startswith('evaluations/')}),
        actual_regression_unique_games=sorted({p['game'] for p in resets if p.get('game') and p['branch'].startswith('regression/')}),
        regression_started_branches=sorted({p['branch'] for p in resets if p['branch'].startswith('regression/')}),
        returned_suffix_actions=sum(p['phase'] == 'suffix' for p in returned.values()),
        failed_attempts=list(errors.values()), unknown_action_numbers=sorted(set(started)-set(returned)-set(errors)),
        note='All ENV_ACTION_STARTED records count, including prefix replays, failed and unknown attempts. Resets are reported separately; no missing attempt is inferred as successful.')


def public_progress_damage(case, branch_result):
    """Conservative descriptive check of explicitly observed goal deliveries.

    A lost earlier delivery is counted only when the number of publicly known
    target items at suitable destinations has decreased at the stopped state.
    Moving them to another suitable destination restores this public count.
    """
    target = re.search(r'\b(?:in|on)\s+(?:a |the )?([a-z]+)\s*\.?$', case['goal'].lower())
    group = case['task'].get('group', '').split('-')
    if not target or len(group) < 2:
        return dict(confirmed=False, assessed=False, reason='public target grammar not identified')
    obj = group[1].lower(); destination = target[1]; positions = {}; evidence = []
    def apply(step, suffix=False):
        text = step['observation']
        move = re.fullmatch(r'You move the (.+?) to the (.+?)\.', text)
        take = re.fullmatch(r'You pick up the (.+?) from the (.+?)\.', text)
        if move and move[1].rsplit(' ',1)[0].lower() == obj:
            positions[move[1]] = move[2]
            if suffix: evidence.append(dict(action=step['action'], observation=text))
        elif take and take[1].rsplit(' ',1)[0].lower() == obj:
            positions[take[1]] = None
            if suffix: evidence.append(dict(action=step['action'], observation=text))
    def placed(): return sorted(k for k,v in positions.items() if v and v.rsplit(' ',1)[0].lower() == destination)
    for step in case['steps']: apply(step)
    before = placed()
    for step in branch_result['steps'][len(case['steps']):]: apply(step, True)
    after = placed()
    return dict(confirmed=not branch_result['won'] and len(after) < len(before), assessed=True,
        checkpoint_known_placed_items=before, final_known_placed_items=after, evidence=evidence,
        limitation='Only explicit public delivery/pickup observations are assessed. A false value does not prove absence of other harm; this is not a hidden-state or task-success oracle.')


def regression_rows(root):
    cases = {x['id']:x for x in read(root/'regression.json')}; rows = []
    for path in sorted((root/'regression').glob('*/*/*/analysis.json')):
        value = read(path); s = value['summary']; result = read(path.parent/'result.json')
        actions = [r['feedback']['action'] for r in result['records']]
        observe = bool(actions) and all(a.strip().lower() in ('look','inventory') or a.strip().lower().startswith('examine ') for a in actions)
        if s['declined_without_action']: category = 'ZERO_ACTION_DECLINE'
        elif observe: category = 'OBSERVATION_ONLY'
        elif s['environment_won']: category = 'TAKEOVER_COMPLETED'
        elif actions: category = 'TAKEOVER_NOT_COMPLETED'
        else: category = 'NO_ACTION_NON_DECLINE'
        damage = public_progress_damage(cases[value['checkpoint_id']]['case'], result)
        rows.append(dict(version=s['executed_version'], group=value['group'], checkpoint_id=value['checkpoint_id'],
            game=value['game'], role=value['role'], category=category, environment_won=s['environment_won'],
            used_actions=s['used_actions'], remaining_actions=s['remaining_actions'],
            stop_reason=s['stop_reason'], exit_reason=s['exit_reason'], false_completion_claim=s['false_completion_claim'],
            runtime_errors=s['runtime_errors'], budget_exhausted=s['remaining_actions'] == 0,
            confirmed_public_progress_damage=damage['confirmed'], progress_damage_evidence=damage,
            historical_G_reexecuted=False, analysis_path=str(path)))
    return rows


def version_rows(root, models):
    rows = []; requests = {x['version']:x for x in models['rows']}
    for path in sorted((root/'candidates').glob('*/submission.json')):
        sub = read(path); version = sub['version']; evaluation = optional(root/'evaluations'/version/'evaluation.json')
        branches = evaluation['branches'] if evaluation else []
        summaries = [b['summary'] for b in branches]
        by_source = {b['source_sequence']:b for b in summaries}
        source_rows = {str(n):by_source.get(n) for n in (41,12,107)}
        boundary = by_source.get(23); cost = requests.get(version)
        code_path = Path(sub['code_path']) if sub.get('code_path') else None
        if code_path and sha(code_path) != sub['code_sha256']: raise ValueError('candidate source changed: '+version)
        rows.append(dict(version=version, group=group_of(version), code_path=str(code_path) if code_path else None,
            code_sha256=sub.get('code_sha256'), unique_source_extracted=isinstance(sub['extraction'].get('code'),str),
            delivery_pass=sub['extraction']['passed'],
            delivery_errors=sub['extraction']['errors'], static_pass=sub['static']['passed'], static_errors=sub['static'].get('errors', []),
            evaluation_complete=evaluation is not None, actual_execution=bool(branches),
            historical_execution_reused=bool(evaluation and evaluation['source_reused']),
            executed_this_run=bool(branches and not evaluation['source_reused']),
            source_41_completed=source_rows['41']['environment_won'] if source_rows['41'] else None,
            source_12_completed=source_rows['12']['environment_won'] if source_rows['12'] else None,
            source_107_completed=source_rows['107']['environment_won'] if source_rows['107'] else None,
            boundary_zero_action_decline=boundary['declined_without_action'] if boundary else None,
            development_pass=evaluation['passed'] if evaluation else None,
            false_completion_claim=any(b['false_completion_claim'] for b in summaries),
            false_completion_evidence=[dict(sequence=b['source_sequence'],reason=b['exit_reason']) for b in summaries if b['false_completion_claim']],
            total_skill_actions=sum(b['used_actions'] for b in summaries), source_branches=source_rows, boundary=boundary,
            new_model_request=cost, new_logical_requests=1 if cost else 0,
            new_actual_model_requests=int(cost['actual_send']) if cost else 0,
            new_provider_usage=cost['usage'] if cost else None,
            new_conservative_cost_microusd=cost['conservative_cost_microusd'] if cost else 0))
    return rows


def summarize(root, report, allow_incomplete=False):
    root, report = Path(root).resolve(), Path(report).resolve()
    completed = optional(root/'Completed.json'); closure = optional(root/'Closure.json')
    if not completed and not closure and not allow_incomplete:
        raise RuntimeError('wait for Completed.json; after a stopped run explicitly use --allow-incomplete')
    protocol = read(root/'protocol.json'); initial = read(report/'Initial_Asset_Counts.json')
    account = budget_account(root); models = model_account(root, account); env = environment_account(root)
    versions = version_rows(root, models); regression = regression_rows(root)
    legacy = optional(root/'Legacy_Revision_Diagnostic.json'); selected = optional(root/'Selected_Candidates.json')
    chains = [read(p) for p in sorted((root/'chains').glob('*.json'))]
    worker_paths = list((root/'evaluations').rglob('workers/*.json'))+list((root/'evaluations').rglob('exclusion_worker.json'))+list((root/'regression').rglob('workers/*.json'))
    branch_ids = {str(p.parent.parent.relative_to(root)) if p.parent.name == 'workers' else str(p.parent.relative_to(root)) for p in worker_paths}
    new_evaluations = [read(p) for p in (root/'evaluations').glob('*/evaluation.json') if not read(p)['source_reused']]
    completed_feedback_branches = sum(len(v['branches']) for v in new_evaluations)+len(regression)
    feedback = dict(new_completed_branch_summaries=completed_feedback_branches,
        new_development_branch_summaries=sum(len(v['branches']) for v in new_evaluations),
        new_regression_branch_summaries=len(regression),
        new_branches_with_worker_feedback=len(branch_ids), new_action_feedback_records=env['returned_suffix_actions'],
        new_development_action_feedback_records=sum(v.get('suffix_returned_actions',0) for k,v in env['by_branch'].items() if k.startswith('evaluations/')),
        new_regression_action_feedback_records=sum(v.get('suffix_returned_actions',0) for k,v in env['by_branch'].items() if k.startswith('regression/')),
        new_worker_feedback_receipts=len(worker_paths),
        new_development_worker_receipts=sum(p.is_relative_to(root/'evaluations') for p in worker_paths),
        new_regression_worker_receipts=sum(p.is_relative_to(root/'regression') for p in worker_paths),
        new_worker_budget_calls=account['totals'].get('worker_calls', 0),
        reused_v0_branch_summaries=4 if any(v['historical_execution_reused'] for v in versions) else 0,
        reused_v0_worker_receipts=initial['legacy_v0_reuse']['total_worker_calls'],
        note='Branch summaries, action observations and Worker decisions are different units; none increases original game/trajectory counts. Partial branches with receipts remain counted even without a completed summary.')
    material = read(root/'learning_input.json')
    if len(material['episodes']) != 3 or sum(len(e['steps']) for e in material['episodes']) != 131:
        raise ValueError('original learning source counts changed')
    data = dict(status='FINAL' if completed or closure else 'STOPPED_OR_INCOMPLETE',
        roles={k:initial[k] for k in ('learning_sources','development_boundary','regression_checkpoints')},
        source_counts=initial['counts'],
        source_counts_scope='Available previously exposed sources: 12 unique games and 10 available regression checkpoints do not mean 12 games or 10 checkpoints were executed in this run.',
        new_feedback_counts=feedback,
        new_activity_counts=dict(new_collected_games=0,new_logical_revision_requests=models['totals'].get('logical_requests',0),
            new_actual_model_requests=account['totals'].get('actual_model_sends',0),
            new_candidate_versions=sum(v['group'] in ('SUMMARY','TRACE') for v in versions),
            legacy_candidate_versions=sum(v['group']=='LEGACY_DIAGNOSTIC' for v in versions),
            recorded_environment_resets=env['totals'].get('recorded_resets',0),
            actual_environment_unique_games=len(env['actual_unique_games']),
            actual_development_unique_games=len(env['actual_development_unique_games']),
            actual_regression_unique_games=len(env['actual_regression_unique_games']),
            regression_branch_evaluations_started=len(env['regression_started_branches']),
            regression_branch_evaluations_completed=len(regression),
            actual_completed_regression_checkpoints=len({r['checkpoint_id'] for r in regression}),
            environment_action_attempts=env['totals'].get('started_actions',0),worker_calls=account['totals'].get('worker_calls',0)),
        project_cumulative_deduplicated_count='累计去重数尚未核实',counting_rules=initial['counting_rules'])
    regression_summary = {}
    for version in sorted({r['version'] for r in regression}):
        by_role = {}
        for role in ('NORMAL_PROGRESS_CONTROL','CONTROLLED_RETAKE'):
            values = [r for r in regression if r['version']==version and r['role']==role]
            by_role[role] = dict(evaluated=len(values), category_counts=dict(Counter(r['category'] for r in values)),
                skill_only_completed=sum(r['environment_won'] for r in values),
                confirmed_public_progress_damage=sum(r['confirmed_public_progress_damage'] for r in values),
                budget_exhausted=sum(r['budget_exhausted'] for r in values),
                runtime_error_branches=sum(bool(r['runtime_errors']) for r in values),
                false_completion_claims=sum(r['false_completion_claim'] for r in values))
        regression_summary[version] = by_role
    expected_checkpoints = {x['id'] for x in read(root/'regression.json')}
    coverage = [dict(version=choice['version'], expected_checkpoints=len(expected_checkpoints),
        completed_checkpoints=sum(r['version']==choice['version'] for r in regression),
        not_evaluated_checkpoints=sorted(expected_checkpoints-{r['checkpoint_id'] for r in regression if r['version']==choice['version']}))
        for choice in (selected or {}).get('candidates', [])]
    chain_outcomes = []
    for group in ('SUMMARY','TRACE'):
        evaluated = sorted([v for v in versions if v['group']==group],key=lambda v:int(v['version'].rsplit('r',1)[1]))
        passing_41 = next((v['version'] for v in evaluated if v['source_41_completed']),None)
        chain_outcomes.append(dict(group=group, evaluated_versions=[v['version'] for v in evaluated if v['evaluation_complete']],
            logical_requests=models['by_group'].get(group,{}).get('logical_requests',0),
            actual_model_sends=models['by_group'].get(group,{}).get('actual_sends',0),
            first_41_success_version=passing_41,
            first_41_success_request_number=int(passing_41.rsplit('r',1)[1]) if passing_41 else None,
            first_full_pass=next((v['version'] for v in evaluated if v['development_pass']),None),
            pre_send_input_rejections=[x for x in models['pre_send_input_rejections'] if x['group']==group],
            all_three_revision_evaluations_completed=len([v for v in evaluated if v['evaluation_complete']])==3))
    result = dict(status='COMPLETE' if completed else (closure['status'] if closure else 'STOPPED_OR_INCOMPLETE'),run_id=protocol['run_id'],
        completed=completed, closure=closure, stopped_records=[read(p) for p in sorted(root.glob('Stopped_*.json'))],
        protocol_sha256=digest(protocol), analyzer_sha256=sha(__file__),
        legacy_stage=legacy and dict(selected=legacy['selected'],stage_two_required=legacy['stage_two_required'],new_model_requests=legacy['new_model_requests']),
        versions=versions, chains=chains, revision_chain_outcomes=chain_outcomes, selected=selected,
        regression=dict(rows=regression, by_version_and_role=regression_summary, candidate_coverage=coverage,
            results_are_exposed_regression=True,native_fallback_calls=0,
            zero_action_decline_means='Checkpoint unchanged by skill; not a newly executed G+skill win.',
            controlled_success_means='Skill completion of an explicitly controlled retake, not rescue of a natural full failure.',
            missing_evaluations='Not tested; never counted as failed or repaired.'),
        new_feedback_counts=feedback, model_accounting=models, environment_accounting=env,
        budget={k:v for k,v in account.items() if k!='requests'},
        legacy_historical_reference=initial['preserved_old_results'],
        conclusion_scope='Learning from actual failure and recovery processes. Two revision chains are exploratory, not independent replications; this exposed regression cannot establish independent transfer.')
    commit(report/'Data_Roles_and_Counts.json',data)
    if legacy is not None: commit(report/'Legacy_Revision_Diagnostic.json',legacy)
    commit(report/'Results.json',result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output','--run',dest='root',type=Path,default=OUT)
    parser.add_argument('--report',type=Path,default=REPORT)
    parser.add_argument('--allow-incomplete',action='store_true')
    args = parser.parse_args(); result = summarize(args.root,args.report,args.allow_incomplete)
    print(json.dumps(dict(status=result['status'],versions=len(result['versions']),
        regression_rows=len(result['regression']['rows']),usage=result['model_accounting']['totals'],
        environment=result['environment_accounting']['totals'],budget=result['budget']['totals']),ensure_ascii=False))
