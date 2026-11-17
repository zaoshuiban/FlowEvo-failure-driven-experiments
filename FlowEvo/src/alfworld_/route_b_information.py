"""Route B public information arms. No model transport, oracle, or environment.

A packet is accepted only if reconstructed from the frozen original receipts.
Success/failure selection remains host-side. No recovery suffix or prior code is
provided to the primary Failure arm. The full task roster is shared by all arms.
"""
from pathlib import Path
from failure_evo.evidence import EvidenceStore
from failure_evo.contracts import fingerprint, canonical
from failure_evo.math_stream import read, sha
from alfworld_.skill_acquisition import load_source

VERSION='route-b-information-v1'
ARMS=('T','S','F')
SYSTEM='''Study the provided task descriptions and optional public historical interactions.
Independently propose a reusable deterministic environmental recovery policy, or abstain.
Distinguish observed behavior from uncertain causes. Do not assume a shared cause.
Use environment_operator(context), where context contains goal, observation,
admissible_commands, history (public action/observation pairs), and bounded JSON state.
Return one legal action with status applied, action, state, reason; or status declined,
state, reason. No hidden state, game IDs, filesystem, network, model calls, subprocess,
reflection or dynamic execution. Only top-level imports, literal constants and functions.
Allowed imports: json, math, collections, itertools, functools, re, heapq, bisect,
fractions, statistics. No instance-ID-specific program or fixed source answer.
Return JSON: {"decision":"PROPOSE","code":"complete Python source",
"description":"hypothesis and uncertainty","applicability":"preconditions and exclusions"}
or {"decision":"ABSTAIN","reason":"insufficient evidence"}.
No existing recovery algorithm or reference solution is supplied.'''


def load_cohort(root):
    root=Path(root);protocol,arms,host=load_source(root)
    commits=EvidenceStore(root/'episodes.jsonl').records();episodes=[]
    if len(protocol['tasks'])!=120 or len(commits)!=120:raise PermissionError('incomplete common cohort')
    files={str(p):sha(p) for p in (root/'protocol.json',root/'summary.json',root/'episodes.jsonl')}
    for i,(task,event) in enumerate(zip(protocol['tasks'],commits),1):
        entry=event['payload'];path=root/'episodes'/task['task_id']/'environment.jsonl'
        rows=EvidenceStore(path).records();files[str(path)]=sha(path)
        before=rows[0]['payload'];steps=[x['payload'] for x in rows[1:]];trace=entry['outcome']['trace']
        if (rows[0]['kind']!='RESET' or any(x['kind']!='STEP' for x in rows[1:])
            or len(steps)!=trace['total_steps'] or len(steps)!=len(trace['actions'])
            or not steps or steps[-1]['won']!=trace['success']):raise PermissionError('trajectory integrity')
        if any(any(s[k]!=t[k] for k in ('action','observation','score','done')) for s,t in zip(steps,trace['actions'])):
            raise PermissionError('trace disagrees with receipt')
        public=[];markers=[]
        for j,s in enumerate(steps,1):
            if s['action'] not in before['commands'] or s['observation'].strip()=='Nothing happens.':markers.append(j)
            public.append(dict(step_ref=f'step_{j:03d}',action=s['action'],observation=s['observation'],admissible_before=list(before['commands'])))
            before=s
        anchor=entry['outcome']['use']['L1_actions'] if trace['success'] and entry['outcome']['use']['fallback'] else None
        if anchor is not None and (not 0<anchor<len(steps) or steps[anchor-1]['observation']!='Nothing happens.'):
            raise PermissionError('unverified local failure anchor')
        episodes.append(dict(task_ref=f'task_{i:03d}',goal=trace['goal'],initial_observation=rows[0]['payload']['observation'],
            steps=public,won=trace['success'],anchor=anchor,markers=markers,task=task,
            native_L1_actions=entry['outcome']['use']['L1_actions'],
            source_sha256=event['record_hash'],environment_sha256=sha(path)))
    return dict(version=VERSION,episodes=episodes,files=files,source_root=str(root),
        source_evidence_ids=sorted(host),source_projected_steps=sum(len(x['steps']) for x in host.values()))


def packet(cohort,arm):
    if arm not in ARMS:raise ValueError('unknown information arm')
    examples=[]
    for ep in cohort['episodes']:
        if arm=='S' and ep['won'] and not ep['markers']:
            end=len(ep['steps']);outcome='SUCCESS';complete=True
        elif arm=='F' and not ep['won']:
            end=len(ep['steps']);outcome='EPISODE_FAILURE';complete=True
        elif arm=='F' and ep['anchor'] is not None:
            end=ep['anchor'];outcome='LOCAL_ACTION_INEFFECTIVE';complete=False
        else:continue
        examples.append(dict(task_ref=ep['task_ref'],initial_observation=ep['initial_observation'],
            history_complete=complete,steps=ep['steps'][:end],observed_outcome=outcome))
    return dict(schema_version=VERSION,task_catalog=[dict(task_ref=e['task_ref'],goal=e['goal']) for e in cohort['episodes']],examples=examples)


def validate_packet(value,cohort,arm):
    # Exact reconstruction prevents private fields, suffix injection, relabelling,
    # role swaps, missing/duplicated evidence, and silent evidence selection.
    for path,h in cohort['files'].items():
        if sha(path)!=h:raise PermissionError('frozen original source drift')
    if canonical(value)!=canonical(packet(cohort,arm)):raise PermissionError('information projection differs from original evidence')
    return value


def wire(cohort,arm,*,model='deepseek-flash',temperature=0.6,output_tokens=4096):
    body=validate_packet(packet(cohort,arm),cohort,arm)
    return dict(model=model,messages=[dict(role='system',content=SYSTEM),dict(role='user',content=canonical(body))],
        thinking={'type':'disabled'},temperature=temperature,max_tokens=output_tokens,stream=False,response_format={'type':'json_object'})


def measure(value):
    n=len(canonical(value).encode())
    return dict(wire_bytes=n,conservative_input_upper=n+256,actual_input_tokens=None,
        input_basis='UTF8_BYTES_PLUS_256_RESERVATION_NOT_TOKENIZER',output_upper=value['max_tokens'],sha256=fingerprint(value))


def balanced_packets(cohort,*,per_type=2,max_wire_bytes=262144):
    """Fixed metadata quotas, whole trajectories, no outcome-driven replacement.

    This is a diagnostic task-type matching proposal, not mechanism matching.
    It never inserts extra information into T to equalize token lengths.
    """
    full={a:packet(cohort,a) for a in ARMS}
    by_ref={e['task_ref']:e for e in cohort['episodes']}
    pools={a:{} for a in ('S','F')}
    for arm in pools:
        for row in full[arm]['examples']:
            kind=by_ref[row['task_ref']]['task']['task_type']
            pools[arm].setdefault(kind,[]).append(row)
    kinds=sorted(set(pools['S'])&set(pools['F']))
    chosen={a:[] for a in ARMS};excluded=[]
    for kind in kinds:
        if min(len(pools[a][kind]) for a in pools)<per_type:
            excluded.append(dict(task_type=kind,reason='INSUFFICIENT_DISTINCT_GAMES',counts={a:len(pools[a][kind]) for a in pools}));continue
        for arm in pools:
            ordered=sorted(pools[arm][kind],key=lambda x:fingerprint(['route-b-quota-v1',x['task_ref']]))
            chosen[arm]+=ordered[:per_type]
    result={a:dict(full[a],examples=chosen[a]) for a in ARMS}
    measurements={}
    for a,value in result.items():
        w=wire(cohort,a);w['messages'][-1]['content']=canonical(value);measurements[a]=measure(w)
    return dict(packets=result,measurements=measurements,excluded=excluded,
        selection={a:[x['task_ref'] for x in result[a]['examples']] for a in ARMS},
        size_passed=all(m['wire_bytes']<=max_wire_bytes for m in measurements.values()),
        rules=dict(version='route-b-quota-v1',per_type=per_type,max_wire_bytes=max_wire_bytes,
                   ordering='hash of neutral task ref',overflow='BLOCK_NO_TRUNCATION_OR_REPLACEMENT'),
        status='DIAGNOSTIC_TASK_TYPE_MATCH_ONLY_NOT_A_MECHANISM_BALANCED_TRAINING_FREEZE')
