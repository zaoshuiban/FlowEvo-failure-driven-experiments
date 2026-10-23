"""Zero-API paired G/F diagnostic. Shared history is NOT independent Gate evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo import PersistentBudget
from failure_evo.contracts import PublicFeedback, PublicTaskView, fingerprint
from failure_evo.failure_events import structural_status, checked_public_feedback
from failure_evo.plugin import FailureLearningPlugin
from failure_evo.checkpoint_evaluator import CheckpointEvaluator, resolve_action
from failure_evo.failure_registry import FailureOperator
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
ACCEPTANCE=ROOT/'runs/s12c_functional_20261021_01/worker_acceptance.json'
OPERATOR=ROOT/'runs/s12b3_revision_20261021_01/candidate_1/candidate.py'
ARCHIVE=ROOT/'experiments/flowevo_taco_lcb_20261019/e3_s0_20261020'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def generic(context):
    """Implement the pre-existing frozen b2-generic-retain-v1 rule."""
    if structural_status(context['candidate_code'])=='STRUCTURAL_PASS':
        return dict(status='declined',reason='current candidate structurally complete')
    for row in reversed(context['candidate_ledger']):
        if structural_status(row['code'])=='STRUCTURAL_PASS' and row['public_feedback']['status']=='PUBLIC_PASS':
            return dict(status='applied',selected_candidate_id=row['candidate_id'])
    return dict(status='declined',reason='no publicly verified complete candidate')


def prepare(run,image):
    run.mkdir(parents=True,exist_ok=False)
    inventory=read(ROOT/'runs/s12a2_20261021_01/data/headroom_inventory.json')
    samples={
      'taco_0219':('1\n4 4\n1 4 1\n1 2 1\n2 3 1\n2 4 1\n1 2 3\n','5\n','graph-travel-and-pickup'),
      'taco_0589':('2\n\n3\n\n1 2\n\n2 3\n\n1 2 3\n\n1 2 3\n\n1 3 6\n\n3\n\n1 2\n\n1 3\n\n1 2 3\n\n5 6 3\n\n4 10 12\n','1 2 3\n\n1 2 -1\n','tree-fruit-consumption'),
      'taco_0044':('3\n3\n0 2 3\n2\n0 1000000000\n1\n0\n','-3\n0\n0\n','directed-graph-minimum-cost')}
    events=[json.loads(x) for x in (ARCHIVE/'events.jsonl').read_text().splitlines()]
    cohorts=[]
    for tid,(inp,expected,family) in samples.items():
        entry=next(x for x in inventory['candidates'] if x['current']['event_id'].startswith(tid+':'))
        current=entry['current'];sequence=[]
        for e in events:
            if e['task_id']!=tid:continue
            path=ARCHIVE/e['paths']['code'];assert sha(path)==e['code_sha256']
            sequence.append(dict(event_id=e['event_id'],stage=e['stage'],source_path=str(path.relative_to(ROOT)),sha256=e['code_sha256'],observed_at=e['response_written_utc']))
            if e['event_id']==current['event_id']:break
        assert sequence[-1]['event_id']==current['event_id']
        assert all(e['observed_at']<=current['observed_at'] for e in sequence)
        task_path=ROOT/'datasets/extracted/data/tasks'/(tid+'.json');task=read(task_path)
        assert ' '.join(inp.split()) in ' '.join(task['prompt'].split())
        assert ' '.join(expected.split()) in ' '.join(task['prompt'].split())
        assert task['function_name'] is None
        cohorts.append(dict(checkpoint_id=current['event_id'],task_public=PublicTaskView.project(task).to_dict(),
            current=current,candidate_ledger=sequence,public_cases=[dict(case_id=tid+':public-sample:1',input=inp,expected=expected,comparison='whitespace_token_exact',reference='original statement sample',legal_verified=True,visibility='public')],
            problem_family=family,source_lineage='original-history:'+tid,original_task_sha256=sha(task_path),
            generation_source='flowevo-taco-lcb-20261019-shared-generation-run',role='diagnostic_development_not_gate'))
    write(run/'checkpoints.json',cohorts)
    write(run/'data_audit.json',dict(strict_independence='FAIL_SHARED_GENERATION_SOURCE',task_disjoint_from_operator_generation=True,
        generation_source_disjoint=False,independent_gate_ready=False,hidden_results_used=False,
        selection='First three noninteractive distinct tasks after excluding exposed witnesses and unsuitable scorers, in prior headroom inventory order; chosen before public execution.',
        excluded=dict(taco_0817='interactive protocol; no trustworthy stdin/stdout public evaluator',taco_0310='previously exposed discovery witness',lcb_atcoder_abc371_f='Operator discovery witness',taco_0226='previous design material'),
        denominator='3 tasks, 3 original failure checkpoints; derived states are paired engineering conditions, not independent samples',D_gate=[],D_reg=[],D_test=[]))
    files=[Path(__file__).resolve(),WORKER,ACCEPTANCE,OPERATOR,run/'checkpoints.json',run/'data_audit.json',ROOT/'runs/s12b2_20261021_01/generic_baseline.json']
    files+=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
    files += [ROOT/e['source_path'] for c in cohorts for e in c['candidate_ledger']]
    p=dict(run_id=run.name,image=image,artifact_sha256=sha(OPERATOR),arms=['G','F'],
        B='NOT_RUN native continuation would need separate API authorization',M='NOT_RUN textual-memory continuation would need separate API authorization',
        conditions=['historical_unknown','reconstructed_public','normal_complete_control'],repeats=1,
        scoring='same public samples for ledger validation and host revalidation; no independent correctness claim',
        order='alternate G/F and F/G for successive paired conditions',model_calls=0,
        budget=dict(max_calls=0,max_tokens=0,max_tools=160,max_cost_microusd=0,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=1600000,tool_milliseconds_upper=10000,wall_seconds=1200),
        frozen_files={str(f.relative_to(ROOT)):sha(f) for f in sorted(set(files))})
    p['protocol_hash']=fingerprint(p);write(run/'protocol.json',p)


def execute(run):
    p=read(run/'protocol.json')
    assert p['protocol_hash']==fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
    for f,h in p['frozen_files'].items():assert sha(ROOT/f)==h
    if (run/'budget.jsonl').exists():raise FileExistsError('no automatic repetition')
    budget=PersistentBudget(run/'budget.jsonl',run_id=p['run_id'],protocol_hash=p['protocol_hash'],**p['budget'])
    ev=CheckpointEvaluator(ROOT,budget,image=p['image'],worker_script=WORKER,acceptance_path=ACCEPTANCE)
    card=SimpleNamespace(artifact_path=str(OPERATOR),artifact_sha256=p['artifact_sha256'])
    output=dict(status='RUNNING',pairs=[],ledger_prechecks=[],B='NOT_RUN',M='NOT_RUN',new_api_calls=0,experimental_authorizations=0)
    def save():output['budget']=budget.snapshot();write(run/'result.json',output)
    save()
    for cp in read(run/'checkpoints.json'):
        rows=[]
        for desc in cp['candidate_ledger']:
            code=(ROOT/desc['source_path']).read_text();verdict=ev.judge(code,cp['public_cases'],3)
            feedback=checked_public_feedback(dict(visibility='public',status='PUBLIC_PASS' if verdict['outcome']=='passed' else ('WRONG_ANSWER' if verdict['outcome']=='failed' else 'UNKNOWN'),tests_run=verdict['tests_run'],tests_passed=verdict['tests_passed']))
            rows.append((code,desc['stage'],feedback))
            output['ledger_prechecks'].append(dict(checkpoint=cp['checkpoint_id'],event_id=desc['event_id'],verdict=verdict))
        for condition in p['conditions']:
            plugin=FailureLearningPlugin(None,None,None,stream_id=p['run_id'],synthetic=True)
            plugin.current=dict(ledger=[],observations=[])
            for code,stage,feedback in rows:
                plugin.observe(code,stage,PublicFeedback('UNKNOWN') if condition=='historical_unknown' else feedback,{},time.time())
            current=(ROOT/cp['current']['source_path']).read_text()
            if condition=='normal_complete_control':
                # Latest structurally complete earlier source, selected without using its score.
                current=next(code for code,stage,fb in reversed(rows[:-1]) if structural_status(code)=='STRUCTURAL_PASS')
            context=dict(task_public=cp['task_public'],candidate_code=current,public_feedback=PublicFeedback('UNKNOWN' if current.strip() else 'NO_COMPLETE_CODE').to_dict(),candidate_ledger=plugin.current['ledger'],generation_metadata={},remaining_budget=dict(model_calls=0,operator_seconds=1),hook='before_native_retry',checkpoint_id=cp['checkpoint_id'],registry_snapshot_id='DIAGNOSTIC_ONLY_NO_AUTHORIZATION')
            pair=dict(checkpoint_id=cp['checkpoint_id'],condition=condition,context=context,arms={})
            order=['G','F'] if len(output['pairs'])%2==0 else ['F','G']
            pair['order']=order
            for arm in order:
                before=budget.snapshot();start=time.monotonic()
                raw=generic(context) if arm=='G' else ev._charged('F-operator',lambda:ev.runner.run(card,context,1))
                action_seconds=time.monotonic()-start
                try:
                    proposed=resolve_action(raw,context['candidate_ledger']);contract=True
                except ValueError:proposed=None;contract=False
                verdict=ev.judge(proposed,cp['public_cases'],3) if proposed is not None else None
                accepted=verdict is not None and verdict['outcome']=='passed'
                final=proposed if accepted else current
                after=budget.snapshot()
                pair['arms'][arm]=dict(action=raw,contract_pass=contract,host_revalidation=verdict,replacement_accepted=accepted,
                    final_sha256=hashlib.sha256(final.encode()).hexdigest(),action_seconds=action_seconds,total_seconds=time.monotonic()-start,
                    model_calls=0,tool_calls=after['tool_calls']-before['tool_calls'])
            pair['same_selected_id']=pair['arms']['G']['action'].get('selected_candidate_id')==pair['arms']['F']['action'].get('selected_candidate_id')
            pair['same_final_artifact']=pair['arms']['G']['final_sha256']==pair['arms']['F']['final_sha256']
            output['pairs'].append(pair);save();print(cp['checkpoint_id'],condition,{a:pair['arms'][a]['action']['status'] for a in ['G','F']},flush=True)
    output['status']='COMPLETED_CONDITIONAL_DIAGNOSTIC';output['independent_gate_ready']=False
    output['artifact_unchanged']=sha(OPERATOR)==p['artifact_sha256'];save()


def main():
    a=argparse.ArgumentParser();a.add_argument('--run',required=True);a.add_argument('--prepare',action='store_true');a.add_argument('--image');v=a.parse_args();run=ROOT/v.run
    if v.prepare:
        if not v.image:a.error('--image required for prepare')
        prepare(run,v.image)
    else:execute(run)
if __name__=='__main__':main()
