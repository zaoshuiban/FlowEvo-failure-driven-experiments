"""A4 confirmation readiness: immutable metadata/exposure audit and read-only scoring.

No model calls. No candidate execution before labelled C1 coverage passes.
Historical probes are exposure, including games that yielded no usable label.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'runs/alfworld_a4_exploratory_20261115_01'
COLLECTION = ROOT/'runs/alfworld_a4_checkpoints_20261115_02'
PREP = ROOT/'runs/alfworld_a4_preparation_20261115_01'
VERSION = 'a4-confirmatory-c1-v1'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
def commit(p, x):
    p=Path(p); text=json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2)+'\n'
    if p.exists():
        if p.read_text()!=text: raise PermissionError('immutable output differs: '+str(p))
    else:
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    return x


def dataset_rows(data):
    # Exact original data directories only; no valid_train/added datasets.
    result=[]
    for split in ('train','valid_seen','valid_unseen'):
        for p in sorted((data/'json_2.1.1'/split).glob('*/*/game.tw-pddl')):
            trajectory=p.with_name('traj_data.json'); m=read(trajectory)
            game=str(p.relative_to(data)); scene=m['scene']['scene_num']
            if type(scene)!=int: raise PermissionError('untrusted scene identity')
            result.append(dict(task_id='alf-'+digest(game)[:20], game=game, split=split,
                game_sha256=sha(p), trajectory_sha256=sha(trajectory), scene=scene,
                group=p.parent.parent.name, trial=p.parent.name, task_type=m['task_type']))
    return result


def selected_rows(value):
    if isinstance(value,dict):
        if all(k in value for k in ('game_sha256','trajectory_sha256','group','game')):
            yield value
        else:
            for v in value.values(): yield from selected_rows(v)
    elif isinstance(value,list):
        for v in value: yield from selected_rows(v)


def protection(rows, roots, excluded_root):
    indices=defaultdict(set)
    for r in rows:
        for k in ('game_sha256','trajectory_sha256','task_id'):
            indices[r[k]].add(r['game_sha256'])
    by_hash={r['game_sha256']:r for r in rows}
    hits=defaultdict(set); files={}; malformed=[]; physical=set(); manifests=[]
    token=re.compile(rb'(?<![a-z0-9])(?:[a-f0-9]{64}|alf-[a-f0-9]{20})(?![a-z0-9])')
    # Scan every recorded event under both controlled stores, not only named runs.
    for top in roots:
        for p in sorted(top.rglob('*.jsonl')):
            if p.is_relative_to(excluded_root): continue
            raw=p.read_bytes(); games=set()
            for key in set(token.findall(raw)): games.update(indices.get(key.decode(),set()))
            if games:
                files[str(p)]=sha(p)
                for h in games:hits[h].add('LOG_REFERENCE:'+str(p))
                for line in raw.splitlines():
                    if not line.strip():continue
                    try:
                        obj=json.loads(line)
                    except (ValueError,UnicodeDecodeError):
                        malformed.append(str(p));continue
                    def groups(x):
                        if isinstance(x,dict):
                            for k,v in x.items():
                                if k in ('physical_state_group_id','physical_checkpoint_identity') and isinstance(v,str):physical.add(v)
                                else:groups(v)
                        elif isinstance(x,list):
                            for v in x:groups(v)
                    groups(obj)
        # Frozen allocation is protected even without execution. Do not read
        # entire eligible/excluded inventories as if every row had been used.
        for p in sorted(top.rglob('*.json')):
            if p.is_relative_to(excluded_root):continue
            name=p.name
            if name not in ('protocol.json','learning_protocol.json','selection.private.json',
                            'candidate_pool.private.json','independent_inventory.private.json',
                            'roles.private.json','checkpoint_jobs.private.json'):continue
            try:obj=read(p)
            except (ValueError,UnicodeDecodeError):
                if 'alfworld' in str(p):malformed.append(str(p))
                continue
            if name in ('protocol.json','learning_protocol.json'):
                obj={k:obj.get(k,[]) for k in ('tasks','future_tasks','gate_shards')}
            selected=list(selected_rows(obj)); matched=set()
            for r in selected:
                h=r['game_sha256']
                if h not in by_hash:continue
                current=by_hash[h]
                if any(r.get(k)!=current[k] for k in ('game','trajectory_sha256','group')):
                    raise PermissionError('historical identity drift: '+str(p))
                matched.add(h);hits[h].add('ALLOCATED_OR_RESERVED:'+str(p))
            if matched:files[str(p)]=sha(p);manifests.append(str(p))
    used_scenes={by_hash[h]['scene'] for h in hits}; used_groups={by_hash[h]['group'] for h in hits}
    used_trajectories={by_hash[h]['trajectory_sha256'] for h in hits}
    excluded=[]; eligible=[]
    for r in rows:
        reasons=[]
        if r['game_sha256'] in hits:reasons.append('EXPOSED_OR_RESERVED_GAME')
        if r['trajectory_sha256'] in used_trajectories:reasons.append('EXPOSED_OR_RESERVED_TRAJECTORY')
        if r['group'] in used_groups:reasons.append('EXPOSED_OR_RESERVED_TASK_GROUP')
        if reasons:excluded.append(dict(task=r,reasons=reasons))
        else:eligible.append(dict(task=r,stratum='strict_scene' if r['scene'] not in used_scenes else 'expanded_game_group'))
    return dict(files=files,protected_games=[dict(task=by_hash[h],reasons=sorted(why)) for h,why in sorted(hits.items())],
        protected_scenes=sorted(used_scenes),physical_checkpoint_ids=sorted(physical),
        malformed=sorted(set(malformed)),eligible=eligible,excluded=excluded,
        scope='all local JSONL identities plus frozen allocations; conservative protection, not proof of external/unrecorded absence',
        metadata_manifest_files=manifests)


def coverage(samples):
    output={}; blockers=[]
    for layer in ('strict_scene','expanded_game_group'):
        output[layer]={}
        for label in ('MATCH','DECLINE','UNKNOWN'):
            rs=[x for x in samples if x['stratum']==layer and x['label']==label and x.get('label_status')=='EVIDENCE_REVIEWED']
            stats=dict(records=len(rs),games=len({x['game_sha256'] for x in rs}),
                scenes=len({x['scene_id'] for x in rs}),physical_groups=len({x['physical_state_group_id'] for x in rs}))
            output[layer][label]=stats
            if layer=='strict_scene' and (stats['games']<4 or stats['scenes']<2):
                blockers.append('STRICT_'+label+'_COVERAGE')
    # All three targets frozen as admission criteria, not picked after results.
    return dict(coverage=output,blockers=blockers,passed=not blockers)


def audit(out):
    if not (out/'start_snapshot.private.json').exists():raise PermissionError('start snapshot required')
    data=Path(read(COLLECTION/'protocol.json')['data_root']);rows=dataset_rows(data)
    inv=protection(rows,[ROOT/'runs',Path.home()/'.local/share/flowevo'],out)
    frozen=read(PREP/'Candidate_Freeze.json')
    for name,r in frozen['arms'].items():
        if sha(r['original_path'])!=r['sha256'] or sha(r['snapshot'])!=r['sha256']:raise PermissionError('candidate drift '+name)
    if frozen['arms']['S0']['sha256']!='233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37':raise PermissionError('S0 identity')
    if frozen['arms']['A3b_candidate_0']['sha256']!='5d92dd91b7bec7d514112f6bfef5814f381a4f8670f72a3807e7200b18de22fd':raise PermissionError('A3b identity')
    commit(out/'exposure.private.json',inv)
    oldtasks=read(COLLECTION/'selection.private.json')['tasks']
    events=[json.loads(s) for s in (COLLECTION/'collection.jsonl').read_text().splitlines()]
    started={e['payload']['id'] for e in events if e['kind']=='GAME_STARTED'}
    completed={e['payload']['id'] for e in events if e['kind']=='GAME_COMPLETED'}
    if started!=completed or started!={r['task']['task_id'] for r in oldtasks}:raise PermissionError('old collection incomplete')
    # Freeze metadata-only candidates. No performance, trajectory actions or
    # expected labels are used. Relevant container types are collection scope,
    # never a runtime semantic rule or candidate modification.
    types=('pick_and_place_simple','pick_heat_then_place_in_recep','pick_cool_then_place_in_recep','pick_clean_then_place_in_recep')
    targets=('Cabinet','Drawer','Fridge','Microwave','Safe')
    candidates=[r for r in inv['eligible'] if r['task']['split']=='train' and r['task']['task_type'] in types and r['task']['group'].rsplit('-',2)[-2] in targets]
    counts={s:dict(games=sum(r['stratum']==s for r in candidates),scenes=len({r['task']['scene'] for r in candidates if r['stratum']==s}),
        types=dict(Counter(r['task']['task_type'] for r in candidates if r['stratum']==s))) for s in ('strict_scene','expanded_game_group')}
    summary=dict(version=VERSION,dataset_games=len(rows),protected_games=len(inv['protected_games']),protected_scenes=len(inv['protected_scenes']),
        former_reserved_pool=dict(games=len(oldtasks),environment_started=len(started),environment_completed=len(completed),reusable_unexecuted_games=0),
        candidate_metadata=counts,missing_log_integrity=inv['malformed'],new_checkpoints=0,new_environment_steps=0,paid_requests=0)
    commit(out/'metadata_audit.json',summary);commit(out/'candidate_metadata.private.json',candidates)
    commit(out/'Candidate_Freeze.json',frozen)
    return summary


def scoring_regression(out):
    # Import frozen compatibility implementation, without changing old runner.
    import resume_alfworld_a4_scoring as S
    import run_alfworld_a4_exploratory as E
    samples={s['sample_id']:s for s in read(COLLECTION/'review.private.json')['samples']}
    old=read(OLD/'result.json'); checked=[]; differences=[]
    for row in old['rows']:
        live=row['live']
        if not live:continue
        origin,_=E.origin_for(samples[row['sample_id']]);prefix=origin['steps'][:origin['projected']['anchor']]
        result=S.score_source(origin,prefix,live['decisions'],live['actions'],live['stop'])
        delta={k:dict(old=live.get(k),new=v) for k,v in result.items() if live.get(k)!=v}
        checked.append(dict(arm=row['arm'],sample_id=row['sample_id'],expected=row['expected'],receipt_sha256=digest(live),unchanged=not delta))
        if delta:differences.append(dict(arm=row['arm'],sample_id=row['sample_id'],differences=delta))
    return commit(out/'scoring_regression.json',dict(scorer_path=str(Path(S.__file__).resolve()),scorer_sha256=sha(S.__file__),
        version='FROZEN_A4_COMPATIBILITY_NO_SEMANTIC_CHANGE',checked=len(checked),rows=checked,differences=differences,
        gate_refusals=len(old['rows'])-len(checked),history_unchanged=True,environment_calls=0,worker_calls=0,passed=not differences))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['audit','scoring-regression']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit(a.output.resolve()) if a.command=='audit' else scoring_regression(a.output.resolve())
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows',)},ensure_ascii=False))
