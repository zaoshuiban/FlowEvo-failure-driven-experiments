"""Zero-API freeze proposal only; authorization is deliberately false."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from code_math.discovery_continuation import plan_tasks
from code_math.no_gold import PublicMathTask,solver_messages,CONCISE_SOLVER_SYSTEM,CONCISE_REVIEW_SYSTEM
from failure_evo.workflow_protocol_v2 import prepare,Limits
from failure_evo.contracts import fingerprint

def freeze(out):
    data=ROOT/'reports/math_no_gold_p0_20261027/data/public/discovery.jsonl';old=ROOT/'runs/math_p1p2_20261027_01'
    rows=[json.loads(x) for x in data.read_text().splitlines()]
    plan=plan_tasks(rows,old/'controller.jsonl',old/'solver_budget.jsonl')
    checks=[]
    for row in plan['new_tasks']:
        t=PublicMathTask.parse(row)
        checks.append([prepare(solver_messages(t,prior,profile='concise-v1'),limits=Limits(output_tokens=4096,input_token_upper=32768)).input_upper for prior in (None,'x'*16384)])
    calls=2*len(plan['new_tasks'])
    protocol=dict(version='math-p1-continuation-v1',paid_api_authorized=False,scope='P1 only; P2 separately gated, not auto-launched',
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('code_math','failure_evo','runtime') for p in (ROOT/'FlowEvo/src'/folder).glob('*.py')},
        original_discovery_sha256=hashlib.sha256(data.read_bytes()).hexdigest(),plan=plan,
        model='deepseek-flash',delivery_profile='concise-v1',system_prompts=[CONCISE_SOLVER_SYSTEM,CONCISE_REVIEW_SYSTEM],
        output_tokens=4096,input_upper=32768,temperature=0,thinking=False,calls_per_task=2,feedback_before_lock=False,
        preliminary_max_input_upper=max(max(x) for x in checks),preflight_limitation='placeholder self-review only; actual output checked before each send',
        score_states=['CONFIRMED_CORRECT','CONFIRMED_WRONG','UNVERIFIED','TRUNCATED','EXECUTION_ERROR'],
        mathematical_failure_admission='final CONFIRMED_WRONG only; correct=false; no truncation or uncertain scores',
        p2_condition='at least two distinct confirmed final failures, source provenance checked; no automatic P2 in this version',
        max_calls=calls,proposed_hard_usd=8,quote_basis='P0/P1 2026-10-27 peak quote; recheck before paid launch',
        quote_directional_upper_usd=calls*(32768*.3+4096*1.2)/1e6,reservation_upper_usd=calls*36864*1.2/1e6,
        no_old_budget_transfer=True,stop_conditions=['UNKNOWN','gold leakage','data contamination','Worker fault','hard budget exhaustion'])
    protocol['source_hashes'].update({name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('scripts/prepare_math_p1_continuation.py','scripts/run_math_p1_continuation.py','scripts/tests/test_math_continuation.py')})
    protocol['private_discovery_sha256']=hashlib.sha256((data.parents[1]/'private/discovery.jsonl').read_bytes()).hexdigest()
    out.mkdir(parents=True,exist_ok=False)
    (out/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
    (out/'task_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    (out/'freeze.json').write_text(json.dumps({'protocol_sha256':hashlib.sha256((out/'protocol.json').read_bytes()).hexdigest(),'paid_api_calls':0})+'\n')
    print(json.dumps(dict(new_tasks=len(plan['new_tasks']),old_locked=len(plan['exposed_locked']),quarantined=len(plan['quarantined_started_unlocked']),max_calls=calls,hard_usd=8)))
if __name__=='__main__':freeze(Path(sys.argv[1]).resolve())
