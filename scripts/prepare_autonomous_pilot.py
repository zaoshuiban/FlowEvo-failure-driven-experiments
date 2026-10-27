"""Freeze a bounded development pilot BEFORE any generation; zero model API calls.
Uses only already public development checkpoints, never the 119-task confirmation set.
"""
import argparse,ast,hashlib,json,pathlib,sys,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint,PublicTaskView
from failure_evo.autonomous_mvp import FrozenLinuxBackend,LinuxPublicEvaluator
from s24_input_legality import validate as previous_legality,integers
BASE=ROOT/'reports/s22_action_preference_v1/frozen'
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'

def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,v):p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(canonical(v)+'\n')
def legal(tid,text):
    if not (tid.endswith('r0298') or tid.endswith('r1248') or tid=='taco_0313'):
        return previous_legality(tid,text)
    try:
        a=integers(text)
        if tid.endswith('r0298'):
            n,h=a[:2];ok=1<=n<=2000 and 1<=h<=2000 and len(a)==n+2 and all(0<=v<=2000 for v in a[2:])
        elif tid.endswith('r1248'):
            n,m,k=a[:3];ok=1<=n<=10**12 and 1<=m<=10**12 and 1<=k<=10000 and len(a)==k+3 and all(1<=v<=10**12 for v in a[3:])
        else:
            t=a[0];ok=1<=t<=10000;offset=1;total=0
            for _ in range(t):
                n=a[offset];offset+=1;total+=n
                ok=ok and 1<=n<=100000 and len(a[offset:offset+n])==n and all(1<=v<=10**9 for v in a[offset:offset+n]);offset+=n
            ok=ok and offset==len(a) and total<=100000
        return dict(valid=bool(ok),method='statement input grammar only')
    except (ValueError,IndexError):return dict(valid=False,reason='INPUT_GRAMMAR')

def as_case(packet,role,code=None):
    task=dict(packet['task_public']);task['public_examples']=[dict(input=c['input'],expected=c['expected'],visibility='public',legal_verified=True) for c in packet['public_cases']]
    return dict(case_id=role+':'+packet['task_id'],task=task,code=packet['code'] if code is None else code,
                lineage_id=packet['task_id'],role=role)

def main(output,exclude_illegal=False):
    out=pathlib.Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'tmp').mkdir();tempfile.tempdir=str(out/'tmp')
    packets={i:read(BASE/f'{i:02}.json')['public_checkpoint'] for i in range(1,11)}
    # Fixed before outputs: existing MVP source, then first two complete parseable
    # non-image failure checkpoints >100 chars in S22's already frozen order.
    source=packets[4];assert source['task_id']=='s18_taco-test-91'
    selected=[];funnel=[]
    for i,p in packets.items():
        try:ast.parse(p['code']);syntax=True
        except (SyntaxError,ValueError):syntax=False
        reason=('DISCOVERY_SOURCE' if i==4 else 'IMAGE_PLACEHOLDER' if '[Image]' in p['task_public']['prompt'] else
                'PREVIOUSLY_CONFIRMED_ILLEGAL_PUBLIC_INPUT' if p['task_id'].endswith('r0236') else
                'INCOMPLETE_FRAGMENT' if len(p['code'])<=100 else 'SYNTAX_INVALID' if not syntax else '')
        take=not reason and len(selected)<2
        if take:selected.append(i)
        funnel.append(dict(position=i,task_id=p['task_id'],selected=take,reason=reason or ('FIRST_TWO_FROZEN_ORDER' if take else 'QUOTA_FILLED')))
    assert selected==[6,7]
    # Correct-code controls: first two unused, non-image tasks with accepted refs;
    # the known invalid r0236 is excluded; use reference_0, not best model output.
    controls=[1,8]
    future_plan=read(ROOT/'runs/s24_learning_probe_20261026_01/protocol.json')
    future_packets=[read(ROOT/t['packet_ref']) for t in future_plan['targets']]
    assert [x['task_id'] for x in future_packets]==['s19g_taco-test-549','s19g_taco-train-s00-r0704']
    groups=dict(source=[as_case(source,'source')],independent=[as_case(packets[i],'independent') for i in selected],negative=[],future=[as_case(p,'future') for p in future_packets])
    refs={};reference_hashes={}
    for i in controls:
        tid=packets[i]['task_id'];directory=ROOT/'runs/s19g_train_expansion_20261024_01/tasks'/tid.removeprefix('s19g_')
        refs[tid]=[directory/f'reference_{j}.py' for j in (0,1)]
        for path in refs[tid]:reference_hashes[str(path.relative_to(ROOT))]=sha(path)
        groups['negative'].append(as_case(packets[i],'negative',refs[tid][0].read_text()))
    exclusions=[]
    if exclude_illegal:
        for rows in groups.values():
            for c in rows:
                kept=[]
                for i,test in enumerate(c['task']['public_examples']):
                    result=legal(c['task']['problem_id'],test['input'])
                    if result['valid']:kept.append(test)
                    else:exclusions.append(dict(task_id=c['task']['problem_id'],case_index=i,input_sha256=hashlib.sha256(test['input'].encode()).hexdigest(),reason=result,role=c['role']))
                if not kept:raise ValueError('no legal cases remain; do not replace task')
                c['task']['public_examples']=kept
    save(out/'excluded_illegal_inputs.json',exclusions)
    all_cases=[c for rows in groups.values() for c in rows]
    assert len(all_cases)==len({c['task']['problem_id'] for c in all_cases})==7
    # Freeze task identities and exact programs before doing any new evaluation.
    save(out/'selection.json',dict(rule='Existing MVP source; S22 frozen-order complete non-image repair targets; unused correct reference controls; S24 frozen future order',
        development_exposure=True,source_selected_for_engineering_previously=True,funnel=funnel,
        task_roles={k:[c['task']['problem_id'] for c in rows] for k,rows in groups.items()},reference_files=reference_hashes,
        no_target_model_outcome_selection=True,confirmation_pool_used=False,exclude_illegal_before_model=exclude_illegal,exclusions=exclusions))
    audited=[];backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER);judge=LinuxPublicEvaluator(backend)
    for role,rows in groups.items():
        for c in rows:
            tid=c['task']['problem_id'];checks=[legal(tid,t['input']) for t in c['task']['public_examples']]
            if not all(x['valid'] for x in checks):
                save(out/'failed_legality.json',dict(task_id=tid,checks=checks));raise ValueError('legal test preflight failed; no replacement')
            record=dict(task_id=tid,role=role,legal_checks=checks,case_count=len(checks),code_sha256=hashlib.sha256(c['code'].encode()).hexdigest())
            if role!='future':
                result=judge(PublicTaskView.project(c['task']),c['code']);record['baseline']=result
                if role=='negative':
                    record['second_reference']=judge(PublicTaskView.project(c['task']),refs[tid][1].read_text())
                    if result['status']!='PUBLIC_PASS' or record['second_reference']['status']!='PUBLIC_PASS':
                        save(out/'failed_reference.json',record);raise ValueError('correct control failed; no replacement')
                elif result['status']=='PUBLIC_PASS':
                    save(out/'no_failure.json',record);raise ValueError('historical failure no longer reproducible; no replacement')
            audited.append(record);save(out/'preflight_progress.json',audited)
    # Task URL / normalized statement / program proxy cross-role audit. No score data.
    metadata=read(ROOT/'runs/s20_preparation_20261025_01/task_lineage_manifest.json')
    byid={r['task_id']:r for r in metadata};lineages=[]
    for c in all_cases:
        tid=c['task']['problem_id'];r=byid.get(tid,{})
        lineages.append(dict(task_id=tid,role=c['role'],original_url=r.get('original_url'),
            normalized_statement_sha256=hashlib.sha256(' '.join(c['task']['prompt'].split()).encode()).hexdigest(),
            code_sha256=hashlib.sha256(c['code'].encode()).hexdigest(),lineage_proxy=c['lineage_id'],
            limitation='Distinct task IDs and original URLs where available; not proof against all semantic near-duplicates'))
    assert len({r['normalized_statement_sha256'] for r in lineages})==7
    known_urls=[r['original_url'] for r in lineages if r['original_url']]
    assert len(known_urls)==len(set(known_urls))
    files=[BASE/f'{i:02}.json' for i in range(1,11)]+[ROOT/t['packet_ref'] for t in future_plan['targets']]
    data=dict(version='autonomous-pilot-data-v2' if exclude_illegal else 'autonomous-pilot-data-v1',groups=groups,checks=audited,lineages=lineages,
        worker=backend.manifest(),source_files={str(p.relative_to(ROOT)):sha(p) for p in files},reference_files=reference_hashes,
        excluded_illegal_inputs=exclusions,policy='Development validation withheld from generation; no sealed data loaded; no task replacement; when explicitly enabled exclude inputs solely by statement legality before any API')
    data['data_sha256']=fingerprint(data);save(out/'data.json',data)
    print(json.dumps(dict(status='DATA_FROZEN_ZERO_API',hash=data['data_sha256'],roles={k:[c['task']['problem_id'] for c in rows] for k,rows in groups.items()},new_model_calls=0),indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--exclude-illegal',action='store_true');args=parser.parse_args();main(args.output,args.exclude_illegal)
