"""One-shot frozen-source offline Gate. Zero API; no score-driven revision."""
from run_math_symmetric_repair import *

GATE=OUT/'independent_gate'

def freeze():
    assert read(OUT/'COMPLETE.json')['ready']==6
    GATE.mkdir(exist_ok=False)
    roles=read(PARENT/'roles.json');private={x['task_id']:x for x in read(PARENT/'private.json')}
    cases=[dict(task_id=t['task_id'],problem=t['problem'],supported=True,
        parameters=private[t['task_id']]['parameters'],answer=private[t['task_id']]['gold_answer'],
        review_status='INDEPENDENT_VERIFIED',review='parent frozen independently cross-checked oracle') for t in roles['Gate']]
    # Exact same construction constraints; the requested mathematical quantity is
    # deliberately outside the frozen count-primes interface. No new algorithm.
    targets=['Count composite positive integers','Count all positive integers',
             'Find the sum of all prime positive integers',
             'Find the largest prime positive integer',
             'Count palindromic positive integers',
             'List all prime positive integers']
    for i,target in enumerate(targets):
        original=roles['Gate'][i]['problem']
        assert original.startswith('Count prime positive integers')
        problem=original.replace('Count prime positive integers',target,1).replace('Count distinct integers.','Do not report the count of primes unless that is the requested quantity.')
        cases.append(dict(task_id='semantic-gate-negative-'+str(i),problem=problem,supported=False,parameters={},answer=None,
            review_status='INDEPENDENT_VERIFIED',review='human semantic review: requested quantity differs from count of primes; no gold needed for refusal label',
            derived_from=roles['Gate'][i]['task_id'],independent_original=False))
    dev=read(OUT/'private_development.json');seen={c['task_id'] for group in dev.values() for c in group}
    prompts={c['problem'] for group in dev.values() for c in group}
    assert not seen.intersection(c['task_id'] for c in cases) and not prompts.intersection(c['problem'] for c in cases)
    candidates=[]
    for r in read(OUT/'results.json'):
        d=OUT/r['name'];lock=read(d/'gate_readiness.json');path=d/'repair/revised.py'
        if lock.get('protocol')!=VERSION:raise PermissionError('old protocol receipt cannot authorize a new Gate')
        assert r['ready_for_gate'] and sha(path)==lock['code_sha256']
        candidates.append(dict(operator_id=r['name'],source_path=str(path.resolve()),code_sha256=sha(path),origin='DEEPSEEK'))
    p=dict(version='symmetric-repair-offline-gate-v1',parent_protocol=read(OUT/'freeze.json'),
        candidates=candidates,cases_sha256=fingerprint(cases),script_sha256=sha(__file__),
        qualification='all20 supported computation/map/combined correct; all6 unsupported decline; no errors',
        no_api=True,no_revision=True,provenance='20 parent Gate inputs never executed or sent to repair model;6 new human semantic negatives derived from6 of those20',
        scope='20 independent parameter instances, NOT26 independent original math problems; negative cases share parameter lineage',
        permissions='offline calculation/routing evidence only; no end-to-end Generic comparison, no publication')
    save(GATE/'private_cases.json',cases);save(GATE/'protocol.json',p);save(GATE/'freeze.json',dict(sha256=fingerprint(p)))
    print('GATE FROZEN',fingerprint(p),flush=True)

def run():
    p=read(GATE/'protocol.json');cases=read(GATE/'private_cases.json')
    assert fingerprint(p)==read(GATE/'freeze.json')['sha256'] and fingerprint(cases)==p['cases_sha256']
    assert sha(__file__)==p['script_sha256']
    for a in p['candidates']:assert sha(a['source_path'])==a['code_sha256']
    with (GATE/'STARTED.json').open('x') as f:json.dump(dict(at=time.time()),f)
    b=PersistentBudget(GATE/'budget.jsonl',run_id=OUT.name+':gate',protocol_hash=fingerprint(p),max_calls=0,max_tokens=0,
        max_tools=450,max_cost_microusd=0,token_rate_microusd_per_million=0,tool_cost_upper_microusd=0,
        max_tool_milliseconds=9000000,tool_milliseconds_upper=20000,wall_seconds=3600)
    results=[]
    try:
        for a in p['candidates']:
            v=ComponentValidation(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),b,GATE/(a['operator_id']+'.jsonl'))
            receipt=v.evaluate(a,cases,'Gate');save(GATE/(a['operator_id']+'.json'),receipt)
            pos=[r for r in receipt['rows'] if r['supported']];neg=[r for r in receipt['rows'] if not r['supported']]
            row=dict(name=a['operator_id'],code_sha256=a['code_sha256'],computation_correct=sum(r['computation_correct'] for r in pos),
                parameter_correct=sum(r['parameter_correct'] is True for r in pos),combined_correct=sum(r['combined_correct'] for r in pos),
                false_accept=sum(r['false_accept'] for r in neg),correct_refusal=sum(r['correct_refusal'] for r in neg),
                errors=sum(r['end_to_end']['status']=='ERROR' for r in receipt['rows']),
                passed=all(r['mapping_valid'] and r['computation_correct'] and r['parameter_correct'] is True and r['combined_correct'] for r in pos)
                    and all(r['mapping_valid'] and r['correct_refusal'] and not r['false_accept'] for r in neg),experimental=False)
            results.append(row);save(GATE/'results.json',results);print(row,flush=True)
        save(GATE/'COMPLETE.json',dict(passed=sum(r['passed'] for r in results),candidates=len(results),model_calls=0,experimental=0,budget=b.snapshot()))
    except BaseException as e:
        save(GATE/'STOP.json',dict(type=type(e).__name__,reason=str(e)));raise

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','run'])
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();OUT=args.out.resolve();GATE=OUT/'independent_gate'
    {'freeze':freeze,'run':run}[args.action]()
