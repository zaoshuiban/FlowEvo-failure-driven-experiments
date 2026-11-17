"""Freeze separate historical learning and metadata-only evaluation material."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import random

from alfworld_.failure_learning import context_view
from alfworld_.precondition_diagnostic import NOOP, command, receipt_effect
from alfworld_.recovery_applicability import compatible, placement_goal
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, sha
from run_alfworld_skill_acquisition import GATE_KEYS
from run_alfworld_success_baseline import exposure, game_row
import run_alfworld_python_recovery_feedback as pilot


BASE = Path.home()/'.local/share/flowevo'
ROOT = pilot.ROOT
PARENT = ROOT/'runs/python_recovery_container_pilot_20261112_01'
S0 = ROOT/'runs/python_recovery_decline_revision_20261112_01'
S0_RESULT_SHA = '6a3b3452075a76af2b66c1e17aaefd5d6c4278f88893f1fdacae12467c8891b7'
S0_CODE_SHA = '233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37'
RULES_SHA = '4e87a9720ef2698d42276a8c4ec357199f22ffa8c452bcd44ec55d8249c43662'
TRAIN_FILE = 'historical_training.private.json'
EVAL_FILE = 'independent_inventory.private.json'


def evidence_categories(goal, step, processed):
    """Identify public contrasts without reading any candidate's decisions."""
    parsed = command(step['action'])
    observation, commands = step['observation'], step['commands']
    result = []
    if parsed is not None:
        verb, args = parsed
        if verb=='move' and observation==NOOP:
            result.append(('ACTUAL_NO_EFFECT_MOVE', 'A real placement attempt produced no effect.'))
    goal_parts = placement_goal(goal)
    if goal_parts is None:
        if goal.lower().startswith('examine ') and any(text.startswith('open ') for text in commands):
            result.append(('NON_PLACEMENT_GOAL', 'The observed task requests inspection rather than placement.'))
        return result
    obj, destination, operation = goal_parts
    if parsed is not None and verb=='move':
        pairs = ((obj,args[0]),(destination,args[1]))
        if any(required and actual.number and required.number and required.category==actual.category
               and required.number!=actual.number for required,actual in pairs):
            result.append(('EXPLICIT_INSTANCE_CONFLICT', 'The action conflicts with an explicit goal instance.'))
        if obj and destination and any(compatible(required,actual) is False for required,actual in pairs):
            result.append(('INCOMPATIBLE_NATIVE_PLACEMENT',
                           'This placement differs from the final task goal; it can still be a valid intermediate action.'))
    if parsed is not None and operation and compatible(obj,args[0]) is True and args[0].number:
        if verb=='take' and receipt_effect(parsed,observation)=='TRUE' and (operation,args[0]) not in processed:
            result.append(('PROCESS_NOT_CONFIRMED', 'The object was taken. Its requested processing has no confirmed public receipt at this step.'))
        if verb==operation and receipt_effect(parsed,observation)=='TRUE':
            result.append(('PROCESS_CONFIRMED', 'The requested processing produced a successful public receipt for this object instance.'))
    if destination and destination.number is None:
        opened = {values[0] for text in commands if (item:=command(text)) is not None
                  for verb,values in (item,) if verb=='open' and values[0].category==destination.category}
        if len(opened)>1:
            result.append(('DISTINCT_PUBLIC_INSTANCES', 'Multiple legal open commands have different instances of the requested destination category.'))
    return result


def archived_material(base):
    if sha(S0/'result.json')!=S0_RESULT_SHA:
        raise PermissionError('S0 result identity differs')
    result = read(S0/'result.json')
    source_code = S0/'candidate_0/revision_02/decoded.py'
    if sha(source_code)!=S0_CODE_SHA or result['attempt']['code_sha256']!=S0_CODE_SHA:
        raise PermissionError('S0 source identity differs')
    old, native, events, host, schedule, boundaries, backend = pilot.frozen_real_inputs(
        base, PARENT, container_only=True)
    if (old['boundaries_sha256']!=fingerprint(boundaries)
            or sha(S0/'candidate_0/revision_02/boundaries.private.json')
                !=result['attempt']['boundary_evaluation']['sha256']):
        raise PermissionError('archived boundaries differ')
    return old,native,events,host,schedule,boundaries,backend,result


def history_rows(base, rules, excluded_games):
    hits, manifests = defaultdict(list), {}
    excluded = Counter()
    games = set()
    for run_name in rules['historical_runs']:
        root = base/run_name
        protocol = read(root/'protocol.json')
        summary = read(root/'summary.json')
        if summary['status']!='COMPLETED' or summary['protocol_sha256']!=fingerprint(protocol):
            raise PermissionError('historical learning evidence requires a complete committed run')
        manifests.update({str(root/name):sha(root/name) for name in ('protocol.json','summary.json','episodes.jsonl')})
        commits = [row for row in EvidenceStore(root/'episodes.jsonl').records()
                   if row['kind']=='EPISODE_COMMITTED']
        for sequence,(task,entry) in enumerate(zip(protocol['tasks'],commits,strict=True),1):
            record = entry['payload']
            if record['task_id']!=task['task_id'] or record['seq']!=sequence:
                raise PermissionError('historical task order differs')
            game = task['game_sha256']
            if game in excluded_games or game in games:
                excluded['archived_sources_or_boundary_game' if game in excluded_games else 'repeated_game']+=1
                continue
            games.add(game)
            path = root/'episodes'/task['task_id']/'environment.jsonl'
            receipt = EvidenceStore(path).records()
            trace = record['outcome']['trace']
            steps = [e['payload'] for e in receipt[1:]]
            if (receipt[0]['kind']!='RESET' or any(e['kind']!='STEP' for e in receipt[1:])
                    or not 1<=len(steps)==trace['total_steps']<=50
                    or any(any(step[k]!=t[k] for k in ('action','observation','score','done'))
                           for step,t in zip(steps,trace['actions'],strict=True))):
                raise PermissionError('historical environment trace differs')
            processed = set()
            for index,step in enumerate(steps,1):
                if step['done']:
                    break
                for category,note in evidence_categories(trace['goal'],step,processed):
                    hits[category].append(dict(run=run_name,sequence=sequence,step=index,task=task,
                        category=category,note=note,goal=trace['goal'],steps=steps[:index],
                        receipt=receipt[index]['record_hash'], journal=str(path)))
                parsed = command(step['action'])
                if parsed and parsed[0] in ('heat','cool','clean') and receipt_effect(parsed,step['observation'])=='TRUE':
                    processed.add((parsed[0],parsed[1][0]))
    selected, used, eligible = [], set(), {}
    for category in rules['priority']:
        eligible[category] = dict(checkpoints=len(hits[category]),
                                  games=len({row['task']['game_sha256'] for row in hits[category]}))
        count = 0
        for row in hits[category]:
            game = row['task']['game_sha256']
            if game in used:
                continue
            used.add(game)
            selected.append(row)
            count+=1
            if count==2:
                break
    return selected,manifests,eligible,dict(excluded)


def freeze_training(base, output):
    rules_path = output/'selection_rules.json'
    if sha(rules_path)!=RULES_SHA:
        raise PermissionError('selection rules differ')
    rules = read(rules_path)
    _, native, _, host, schedule, boundaries, _, _ = archived_material(base)
    _, sources, _ = schedule[0]
    by_sequence = {task['sequence']:task['row'] for task in host.values()}
    # Expanded boundary sources include a navigation game outside the 11 positives.
    excluded = {native['tasks'][i-1]['game_sha256'] for i in
                set(rules['excluded_source_sequences_in_formal_run'])|{b['source_sequence'] for b in boundaries}}
    rows,manifests,eligible,exclusions = history_rows(base,rules,excluded)
    records = []
    for index,row in enumerate(rows,1):
        last = row['steps'][-1]
        context = context_view(row['goal'],last['observation'],last['commands'],row['steps'],{})
        context.pop('state')
        records.append(dict(evidence_ref=f'historical_{index:02d}',public_context=context,
            observation_annotation=row['note'],kind=row['category'],provenance=dict(
                historical_run=row['run'],sequence=row['sequence'],step=row['step'],task=row['task'],
                receipt_sha256=row['receipt'],journal_sha256=sha(row['journal']),journal=row['journal'])))
    positive_scenes = {by_sequence[r['sequence']]['scene'] for r in sources}
    boundary_scenes = {native['tasks'][b['source_sequence']-1]['scene'] for b in boundaries}
    material = dict(selection_rules_sha256=RULES_SHA, archived_sources_sha256=fingerprint(sources),
        historical_manifests=manifests, rows=records, available=eligible, exclusions=exclusions,
        development_scenes=sorted(positive_scenes|boundary_scenes|{r['task']['scene'] for r in rows}),
        exposed_boundary_cases_sha256=fingerprint(boundaries), historical_contexts=len(records))
    return pilot.commit(output/TRAIN_FILE,material)


def destination(row):
    return row['group'].rsplit('-',2)[-2]


def freeze_inventory(base, output, training):
    rules = read(output/'selection_rules.json')['evaluation']
    data = Path(read(base/'alfworld_full_library_online120_20261109_01'/'protocol.json')['data_root']).resolve()
    prior, manifests = exposure(base,data)
    original = read(base/'alfworld_skill_acq_gate_pool_20261109_01'/'candidate_pool.private.json')
    strict = original['candidate_pool']
    used = {key:{row[key] for row in prior} for key in GATE_KEYS}
    if (original['candidate_pool_sha256']!=fingerprint(strict)
            or any(any(row[key] in used[key] for key in GATE_KEYS) for row in strict)
            or any(game_row(data/row['game'],data)!=row for row in strict)):
        raise PermissionError('strict-scene pool drift')
    prohibited_scenes = set(training['development_scenes'])|{row['scene'] for row in strict}
    reserved_groups = {row['group'] for row in strict}
    candidates = defaultdict(list)
    for path in sorted((data/'json_2.1.1/train').glob('*/*/game.tw-pddl')):
        row = game_row(path,data)
        if (row['scene'] in prohibited_scenes or row['group'] in reserved_groups
                or any(row[key] in used[key] for key in GATE_KEYS[:-1])):
            continue
        kind = destination(row)
        stratum = kind if kind in rules['target_strata'] else 'OTHER'
        candidates[stratum].append(row)
    rng = random.Random(rules['seed'])
    expanded = []
    for stratum,cap in rules['target_strata'].items():
        rows = candidates[stratum]
        rng.shuffle(rows)
        scenes, count = Counter(), 0
        for row in rows:
            if row['group'] in reserved_groups or scenes[row['scene']]>=2:
                continue
            reserved_groups.add(row['group'])
            scenes[row['scene']]+=1
            expanded.append(dict(row,stratum=stratum,project_scene_previously_exposed=row['scene'] in used['scene']))
            count+=1
            if count==cap:
                break
    all_rows = strict+expanded
    if any(len({row[k] for row in all_rows})!=len(all_rows) for k in GATE_KEYS[:2]):
        raise PermissionError('evaluation duplicate game or trajectory')
    return pilot.commit(output/EVAL_FILE,dict(
        status='METADATA_ONLY_CHECKPOINT_LABELS_REQUIRED', strict_scene=strict, expanded_game_group=expanded,
        strict_sha256=fingerprint(strict),expanded_sha256=fingerprint(expanded),seed=rules['seed'],
        provenance_manifests=manifests,known_exposed_games=len(prior),game_hashes_disjoint=True,
        development_scenes=training['development_scenes'],eligible={k:len(v) for k,v in candidates.items()},
        games_executed=0,used_for_learning=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('training','evaluation'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base', type=Path, default=BASE)
    args = parser.parse_args()
    output = args.output.resolve()
    if sha(output/'selection_rules.json')!=RULES_SHA or output.stat().st_mode&0o077:
        raise PermissionError('private frozen role directory required')
    if args.command=='training':
        result = freeze_training(args.base,output)
        print(dict(rows=result['historical_contexts'], available=result['available'],
                   retained=dict(Counter(row['kind'] for row in result['rows'])), sha256=sha(output/TRAIN_FILE)))
    else:
        result = freeze_inventory(args.base,output,read(output/TRAIN_FILE))
        print(dict(strict=len(result['strict_scene']),expanded=len(result['expanded_game_group']),
                   strata=dict(Counter(row['stratum'] for row in result['expanded_game_group'])),
                   eligible=result['eligible'],sha256=sha(output/EVAL_FILE)))


if __name__=='__main__':
    main()
