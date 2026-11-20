"""Inventory and freeze a bounded TACO function subset without model requests."""
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'FlowEvo/src'),str(REPO/'runs/taco_function_acquisition_20261120/preparation/python_deps')]
from env.taco_function_loader import signature,public_examples,json_value,assertion
from failure_evo.contracts import fingerprint
from failure_evo.pilot_runtime import write_json

ROOT=REPO/'runs/taco_function_acquisition_20261120/preparation'
OUT=REPO/'reports/taco_function_acquisition_20261120'


def norm(s):return ' '.join(re.findall(r'[a-z0-9]+',s.lower()))


def stratum(row):
    # Sampling hypotheses only; never included in the model's public task.
    words=norm(str(row.get('tags'))+' '+str(row.get('skill_types')))
    if any(x in words for x in ['dynamic programming','complete search','graph','tree']):return 'state_and_search'
    if any(x in words for x in ['math','number theory','bit manipulation']):return 'numeric_operations'
    return 'sequence_and_string'


def inventory():
    import pyarrow.parquet as pq
    OUT.mkdir(parents=True,exist_ok=True)
    raw=pq.read_table(ROOT/'taco_train_shard00.parquet').to_pylist()
    local=[]
    for p in (REPO/'experiments/flowevo_taco_lcb_20261019/audit/data/tasks').glob('taco_*.json'):
        local.append(json.loads(p.read_text()))
    seen_prompts={norm(r['prompt']) for r in local}
    local_functions=[r for r in local if r.get('function_name')]
    counts=Counter();excluded=[];eligible=[]
    version=json.loads((ROOT/'download_receipt.json').read_text())
    for index,r in enumerate(raw):
        try:io=json.loads(r['input_output'])
        except (ValueError,TypeError):continue
        if not io.get('fn_name'):continue
        counts['supplement_function_tasks']+=1
        try:
            spec=signature(r['starter_code'],io['fn_name'])
            counts['interface_supported']+=1
            if not io['inputs'] or len(io['inputs'])!=len(io['outputs']):raise ValueError('MISSING_OR_INCONSISTENT_SCORING')
            examples=public_examples(r['question'],spec)
            if not examples:raise ValueError('NO_EXPLICIT_PUBLIC_LITERAL_EXAMPLES')
            counts['public_validation_permission_clear']+=1
            # Exact-return comparator cannot judge intentionally nonunique answers.
            if re.search(r'return any|any valid|in any order|any one of|any order|any of the possible',r['question'],re.I):
                raise ValueError('SPECIAL_JUDGE_REQUIRED')
            if r['source'] not in {'leetcode','codewars'}:raise ValueError('UNREVIEWED_RETURN_ENCODING')
            if r.get('picture_num') not in (None,'0',0,'') and '<image>' in r['question']:raise ValueError('IMAGE_DEPENDENT')
            cases=[]
            for args,value in zip(io['inputs'],io['outputs']):
                if not isinstance(args,list) or not spec['required']<=len(args)<=len(spec['parameters']):raise ValueError('INVALID_ARGUMENT_ARRAY')
                if r['source']=='codewars':
                    if not isinstance(value,list) or len(value)!=1:raise ValueError('INVALID_RETURN_ENVELOPE')
                    value=value[0]
                if not json_value([args,value]):raise ValueError('FLOAT_OR_CUSTOM_COMPARATOR_REQUIRED')
                cases.append(dict(args=args,kwargs={},expected=value))
            if len(json.dumps(cases))>48000:raise ValueError('SCORING_INPUT_BOUND')
            for ex in examples:
                if any(ex['args']==c['args'] and not ex['kwargs'] and ex['expected']!=c['expected'] for c in cases):
                    raise ValueError('PUBLIC_PRIVATE_REFERENCE_CONFLICT')
            url=r.get('url')
            if not url or not urlsplit(url).hostname:raise ValueError('MISSING_SOURCE_LINEAGE')
            if norm(r['question']) in seen_prompts:raise ValueError('PREVIOUS_LOCAL_EXPOSURE')
            solutions=json.loads(r['solutions'])
            reference=next((s for s in solutions if isinstance(s,str) and s.strip()),None)
            if reference is None:raise ValueError('NO_SCORER_POSITIVE_CONTROL')
            ast.parse(reference)
            tid='TACO/train/shard00/'+str(index)
            public=dict(problem_id=tid,benchmark='taco',upstream_split='train',row_index=index,
                data_version=version,public_problem=r['question'],starter_code=r['starter_code'],
                call_protocol=spec,public_cases=examples,source_url=url,
                source_lineage_id=url.rstrip('/'),duplicate_group_id=url.rstrip('/'),
                capability_family_id=stratum(r),difficulty=r['difficulty'],
                exposure_status='not_run_by_this_project; public metadata audited',
                validation_permission='statement examples only; independent train scoring binary under new protocol')
            folder=ROOT/'private_data'/str(index);folder.mkdir(parents=True,exist_ok=True)
            scoring=dict(cases=cases,source_encoding=r['source'],original_input_output_sha256=fingerprint(io))
            write_json(folder/'scoring.json',scoring)
            (folder/'positive_control.py').write_text(reference)
            public.update(private_scoring_ref=str((folder/'scoring.json').relative_to(REPO)),
                private_scoring_sha256=hashlib.sha256((folder/'scoring.json').read_bytes()).hexdigest(),
                positive_control_ref=str((folder/'positive_control.py').relative_to(REPO)),
                private_case_count=len(cases),public_example_count=len(examples))
            eligible.append(public)
        except (ValueError,TypeError,KeyError,SyntaxError,StopIteration) as e:
            excluded.append(dict(row_index=index,entry_point=io['fn_name'],reason=str(e)))
    # Deterministic source / near-description groups; components never cross roles.
    parent=list(range(len(eligible)))
    def find(i):
        while parent[i]!=i:i=parent[i]
        return i
    tokens=[norm(r['public_problem']).split() for r in eligible]
    shingles=[set(zip(t,t[1:],t[2:],t[3:])) for t in tokens]
    edges=[]
    for i in range(len(eligible)):
        for j in range(i):
            same=eligible[i]['source_lineage_id']==eligible[j]['source_lineage_id']
            overlap=len(shingles[i]&shingles[j])/max(1,len(shingles[i]|shingles[j]))
            if same or overlap>=0.65:
                parent[find(i)]=find(j);edges.append(dict(a=eligible[i]['problem_id'],b=eligible[j]['problem_id'],reason='source_url' if same else 'description_4gram',jaccard=overlap))
    unique=[];used=set()
    for i,row in enumerate(eligible):
        group=find(i)
        row['duplicate_group_id']='taco-near-'+fingerprint(eligible[group]['source_lineage_id'])[:16]
        if group not in used:unique.append(row);used.add(group)
    counts['schema_and_permission_qualified']=len(eligible)
    counts['source_and_near_deduplicated']=len(unique)
    summary=dict(local_assets=dict(unique_tasks=len(local),function_tasks=len(local_functions),
                       historical_permissions='not relabeled; old full scoring remains diagnostic only'),
        supplement=dict(inspected_rows=len(raw),**dict(counts)),exclusion_counts=dict(Counter(r['reason'] for r in excluded)),
        version=version,near_duplicate_edges=edges,
        note='No claim of exhaustive semantic deduplication; finite public-description/source audit. Public task roles freeze after scorer controls, before Actor calls.')
    write_json(OUT/'Inventory.json',summary)
    write_json(ROOT/'candidate_pool.json',unique)
    write_json(ROOT/'excluded.json',excluded)
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':inventory()
