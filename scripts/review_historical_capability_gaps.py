"""Bounded post-hoc review: archived public tasks and frozen operators only.

No model client, network request, learner, admission or future-task loader.
Candidate code executes only through the existing MathOperatorRunner/Docker backend.
Private reference recomputation stays outside candidate execution and learning artifacts.
"""
import argparse
import ast
import collections
import hashlib
import json
import math
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'FlowEvo/src'))
from failure_evo.contracts import fingerprint
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.math_operators import MathOperatorRunner, validate_math_source
from failure_evo.persistent_budget import PersistentBudget
from code_math.no_gold import PublicMathTask

RUN = REPO / 'runs/historical_capability_gap_review_20261120'
OUT = REPO / 'reports/historical_capability_gap_review_20261120'
P2 = REPO / 'runs/math_p2_all12_20261027_01'
P3 = REPO / 'runs/math_p3_functional_audit_20261027_01'
DATA = REPO / 'reports/math_no_gold_p0_20261027/data'
GOOD = '43cda71416fe598643a93400f493c22ad510b0e5232a44d5927cbe2d9ebe43f8'
BAD = '90421062837425d60693ba5c8325c1ff5dec35ca13a63805366a24e97dbd9098'

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return str(p.relative_to(REPO))
def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def lines(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]

def prepare():
    if RUN.exists(): raise RuntimeError('Review already prepared; no replacement')
    f = read(P3/'freeze.json')
    assert fingerprint(f) == read(P3/'freeze_receipt.json')['sha256']
    assert sha(P3/'outputs_locked.json') == read(P3/'outputs_lock.json')['sha256']
    scores, outputs = read(P3/'scores.json'), read(P3/'outputs_locked.json')
    sources = [x for x in read(P2/'source_failures.json') if 'parenthes' in x['task']['problem'].lower()]
    assert len(sources) == 5
    jobs = [dict(task=x['task'], role='Source', historical_evidence_id=x['evidence_id']) for x in sources]
    design = [x for x in scores if x['slot']==2 and x['role']=='Design' and x['status']!='DECLINED']
    assert len(design) == 12
    jobs += [dict(task=f['jobs'][x['index']]['task'], role='Exposed_Design', historical_score_index=x['index']) for x in design]
    assert len(jobs)==17 and len({x['task']['task_id'] for x in jobs})==17
    artifacts = [a for a in f['artifacts'] if a['code_sha256'] in (GOOD, BAD)]
    assert len(artifacts)==2
    for a in artifacts:
        assert sha(Path(a['source_path']))==a['code_sha256']
        assert validate_math_source(Path(a['source_path']).read_text())['passed']
    audit=[]
    private_source={x['task_id']:x for x in lines(DATA/'private/discovery.jsonl')}
    hypothesis=read(P2/'normalized_hypothesis.json')['mechanisms']
    for x in sources:
        assert x['scored_after_final_lock'] and not x['gold_exposed']
        assert x['final']['status']=='CONFIRMED_WRONG'
        p=private_source[x['task_id']];m=p['original_metadata']
        assert p['problem_sha256']==x['problem_sha256']==fingerprint(x['task']['problem'])
        audit.append(dict(task_id=x['task_id'],problem=x['task']['problem'],
            original_answer=x['final']['parsed_answer'],final_output_sha256=hashlib.sha256(x['responses'][-1]['text'].encode()).hexdigest(),
            final_output_ref=rel(P2/'source_failures.json')+'#'+x['evidence_id']+'/responses/-1/text',
            evidence_id=x['evidence_id'],locked_sha256=x['locked_sha256'],
            scorer_version=x['scorer_version'],original_verdict=x['final']['status'],
            data_role=p['role'],exposure='P1 solver, P2 induction, candidate source subset, P3 audit; now exposed development',
            source_lineage_id='legacy-source-failure-index:'+','.join(map(str,m['source_failure_indices'])),
            parameter_lineage=p['parameter_lineage'],origin=m['origin'],generator_version=m['generator_version'],
            used_in_induction=True,generated_candidate_slots=[i for i,h in enumerate(hypothesis) if x['evidence_id'] in h['source_event_ids']],
            p3_source_checks=[s for s in scores if s['task_id']==x['task_id'] and s['role']=='Source'],
            prior_original_p0_gate_used=False,independent_original=False))
    tracked=[]
    for d in [P2,P3,REPO/'runs/hard140_algorithm_20261028_01',REPO/'runs/autonomous_reuse_20261120',REPO/'reports/autonomous_reuse_20261120']:
        tracked += [p for p in d.rglob('*') if p.is_file() and not p.name.endswith('.pyc')]
    tracked += list((REPO/'FlowEvo/src').rglob('*.py'))
    tracked += [DATA/'private/discovery.jsonl',DATA/'private/design.jsonl',DATA/'generator_provenance.json',DATA/'manifest.json']
    reference=DATA/'private/original_sources/scripts/baseline_failure_mechanisms_v2.py'
    tracked.append(reference)
    manifest={rel(p):sha(p) for p in sorted(set(tracked))}
    inputs={rel(Path(a['source_path'])):a['code_sha256'] for a in artifacts}
    inputs.update({rel(Path(__file__)):sha(Path(__file__)),rel(reference):sha(reference)})
    inputs.update({rel(REPO/p):sha(REPO/p) for p in ['FlowEvo/src/failure_evo/math_operators.py','FlowEvo/src/failure_evo/container_worker.py','FlowEvo/src/failure_evo/persistent_budget.py']})
    freeze=dict(version='historical-capability-review-v1',created_at=time.time(),jobs=jobs,
        candidate=next(a for a in artifacts if a['code_sha256']==GOOD),artifacts=artifacts,
        worker=f['worker'],input_hashes=inputs,reference_source=rel(reference),
        budget=dict(model_calls=0,teacher_calls=0,worker_jobs=17,wall_seconds=1800,tool_milliseconds=102000),
        selection='all 5 exposed parenthesization source failures and all 12 previously applied P3 Design cases for candidate 3; no newly sampled/generated tasks',
        roles='diagnostic only; no retrospective training permission changes',
        historical_gold_permission='P2 source_gold_scoring=false preserved; P3 authorized diagnosis and current diagnostic replay do not authorize teacher feedback',
        no_revision=True,no_admission=True,no_future_task_access=True)
    save(RUN/'freeze.json',freeze);save(RUN/'freeze_receipt.json',dict(sha256=fingerprint(freeze)))
    save(RUN/'historical_files.json',manifest);save(OUT/'Parenthesization_Sources.json',audit)
    save(OUT/'Historical_P3_Projection.json',dict(summary=read(P3/'summary.json'),
        relevant_scores=[s for s in scores if s['slot'] in (1,2)],
        inputs_validated=True,outputs_lock_verified=True,
        historical_execution_count=156,new_execution_count=0))
    print(json.dumps(dict(stage='PREPARED',jobs=len(jobs),protocol_sha256=fingerprint(freeze),models=0)))

def verify():
    f=read(RUN/'freeze.json')
    assert fingerprint(f)==read(RUN/'freeze_receipt.json')['sha256']
    assert all(sha(REPO/p)==h for p,h in f['input_hashes'].items())
    return f

def execute():
    f=verify()
    if (RUN/'STARTED.json').exists():raise RuntimeError('Consumed audit; no automatic retry')
    save(RUN/'STARTED.json',dict(at=time.time(),protocol_sha256=fingerprint(f)))
    b=PersistentBudget(RUN/'budget.jsonl',run_id=RUN.name,protocol_hash=fingerprint(f),
        max_calls=0,max_tokens=0,max_tools=17,max_cost_microusd=0,
        token_rate_microusd_per_million=0,tool_cost_upper_microusd=0,
        max_tool_milliseconds=102000,tool_milliseconds_upper=6000,wall_seconds=1800)
    runner=MathOperatorRunner(FrozenLinuxBackend(image=f['worker']['image'],worker_script=f['worker']['worker_script']),b)
    results=[]
    try:
        for i,j in enumerate(f['jobs']):
            value=runner.run(f['candidate'],PublicMathTask.parse(j['task']),timeout=2)
            row=dict(index=i,task_id=j['task']['task_id'],role=j['role'],source_sha256=GOOD,result=value)
            save(RUN/'executions'/f'{i:02d}.json',row);results.append(row)
        save(RUN/'outputs_locked.json',results)
        save(RUN/'outputs_lock.json',dict(sha256=sha(RUN/'outputs_locked.json'),count=len(results),at=time.time()))
    except BaseException as e:
        save(RUN/'STOP.json',dict(error=type(e).__name__,detail=str(e),completed=len(results),no_retry=True))
        raise
    print(json.dumps(dict(stage='OUTPUTS_LOCKED',jobs=len(results),model_calls=0)))

def score():
    f=verify();results=read(RUN/'outputs_locked.json')
    assert sha(RUN/'outputs_locked.json')==read(RUN/'outputs_lock.json')['sha256'] and len(results)==17
    if (RUN/'COMPLETE.json').exists():raise RuntimeError('Scoring already closed')
    # Reuse the separately archived exact Fraction oracle, never candidate code.
    source=(REPO/f['reference_source']).read_text()
    fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_parenthesized_values')
    ns=dict(Fraction=Fraction,lru_cache=lru_cache)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),f['reference_source'],'exec'),ns)
    oracle=ns['_parenthesized_values']
    private={x['task_id']:x for file in ['discovery.jsonl','design.jsonl'] for x in lines(DATA/'private'/file)}
    import re
    scored=[];private_receipts=[]
    for j,row in zip(f['jobs'],results):
        text=j['task']['problem'];tid=row['task_id'];p=private[tid]
        assert fingerprint(text)==p['problem_sha256']
        normalized=text.replace('\\cdot','*').replace('\\times','*').replace('×','*')
        expr=max(re.findall(r'\d+(?:\s*[+*\-]\s*\d+)+',normalized),key=len)
        tokens=re.findall(r'\d+|[+*\-]',expr);nums=tuple(map(int,tokens[::2]));ops=tuple(tokens[1::2])
        assert 2<=len(nums)<=7 and len(ops)==len(nums)-1 and set(ops)<={'+','-','*'}
        values=oracle(nums,ops)
        low=text.lower()
        target='minimum' if 'smallest' in low else 'maximum' if 'largest' in low else 'tree_forms' if 'forms separately' in low or 'every parenthesization form' in low else 'distinct_value_count'
        expected=min(values) if target=='minimum' else max(values) if target=='maximum' else Fraction(math.comb(2*(len(nums)-1),len(nums)-1)//len(nums)) if target=='tree_forms' else Fraction(len(values))
        assert expected==Fraction(p['gold_answer']), 'REFERENCE_DISAGREEMENT'
        raw=row['result'];matches=raw['status']=='APPLIED' and Fraction(raw['answer'])==expected
        scored.append(dict(task_id=tid,role=j['role'],target_quantity=target,status='PASS' if matches else 'WRONG_TARGET_ACCEPTED' if raw['status']=='APPLIED' and target!='distinct_value_count' else raw['status'],
            source_sha256=GOOD,source_input_legal=True,independent_reference_agrees_with_archived_score=True,
            private_receipt_ref=rel(RUN/'private/reference_receipts.json')+'#'+tid,
            execution_receipt=rel(RUN/'executions'/f"{row['index']:02d}.json")))
        private_receipts.append(dict(task_id=tid,expected=str(expected),quantity=target,numbers=nums,operators=ops,values=[str(v) for v in sorted(values)],reference_source_sha256=sha(REPO/f['reference_source']),private=True))
    save(RUN/'private/reference_receipts.json',private_receipts)
    old=read(RUN/'historical_files.json');assert all(sha(REPO/p)==h for p,h in old.items())
    ledger=lines(RUN/'budget.jsonl')
    assert not any(e['kind']=='RESERVED' and e['payload']['kind']=='model' for e in ledger)
    worker_ms=sum(e['payload'].get('tool_milliseconds',0) for e in ledger if e['kind']=='SETTLED')
    summary=dict(status='CLOSED_COMPLETED',model_calls=0,teacher_calls=0,new_worker_jobs=17,worker_milliseconds=worker_ms,
        source= dict(collections.Counter(s['status'] for s in scored if s['role']=='Source')),
        exposed_design=dict(collections.Counter(s['status'] for s in scored if s['role']=='Exposed_Design')),
        source_lineages=1,independent_original_support=0,source_unchanged=True,historical_files_unchanged=len(old),
        scope='Fixed exposed diagnostic replay, not new learning, independent transfer, or admission',rows=scored)
    save(OUT/'Math_Operator_Coverage_Result.json',summary)
    save(RUN/'COMPLETE.json',dict(status='CLOSED_COMPLETED',summary_sha256=sha(OUT/'Math_Operator_Coverage_Result.json'),at=time.time()))
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','execute','score']);a=p.parse_args()
    globals()[a.mode]()
