"""Public-only capacity-defect entry gate. No API and no new Operator source."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo import PersistentBudget, FailureEvidenceStore, FailureOperatorRegistry
from failure_evo.contracts import PublicTaskView, PublicFeedback, Fingerprint, fingerprint
from failure_evo.plugin import FailureLearningPlugin
from failure_evo.runtime import Budget, Controller
from failure_evo.checkpoint_evaluator import CheckpointEvaluator, compare_output
from failure_evo.compiler_contract import build_compiler_contract
from failure_evo.generations import generation_decision
from compare_s12_generic_operator import generic
BASE=ROOT/'experiments/flowevo_taco_lcb_20261019/trusted_rgf_20261020'
CF=BASE/'counterfactuals/lcb_atcoder_abc301_f'
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
PROOF=ROOT/'runs/s12c_functional_20261021_01/worker_acceptance.json'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def prepare(run):
    run.mkdir(parents=True,exist_ok=False)
    task_path=ROOT/'datasets/extracted/data/tasks/lcb_atcoder_abc301_f.json';task=read(task_path)
    samples=[('DD??S\n','676\n'),('?'*40+'\n','858572093\n'),('?D??S\n','136604\n')]
    cases=[]
    for i,(inp,expected) in enumerate(samples):
        assert inp.strip() in task['prompt'] and expected.strip() in task['prompt']
        cases.append(dict(case_id='abc301_f:statement:'+str(i+1),input=inp,expected=expected,comparison='whitespace_token_exact',visibility='public',legal_verified=True,reference='original public statement'))
    write(run/'task_public.json',PublicTaskView.project(task).to_dict());write(run/'statement_cases.json',cases)
    # This is an existing legal public counterexample, not an injected program defect.
    assert (CF/'public_input.txt').read_text().strip()=='AaAA'
    write(run/'boundary_case.json',dict(case_id='abc301_f:public-boundary',input='AaAA\n',expected='1\n',comparison='whitespace_token_exact',visibility='public',legal_verified=True,reference='No ? and no repeated-uppercase pair followed by lower then upper; exactly one allowed assignment. Existing public counterexample, now re-executed.'))
    event=next(json.loads(line) for line in (ROOT/'experiments/flowevo_taco_lcb_20261019/e3_s0_20261020/events.jsonl').read_text().splitlines() if json.loads(line)['event_id']=='lcb_atcoder_abc301_f:l1')
    assert event['code_sha256']==sha(CF/'original.py')
    write(run/'source_provenance.json',dict(event_id=event['event_id'],observed_at=event['response_written_utc'],candidate_sha256=event['code_sha256'],source_mode='historical_l1_replay',original_task_sha256=sha(task_path),natural_program_defect=True,synthetic_fault=False,future_candidates_used_in_checkpoint=False))
    sources=[CF/'original.py',CF/'fixed.py',BASE/'rgf_results/programs/01_lcb_atcoder_abc301_f_G_2.py',BASE/'rgf_results/programs/11_lcb_atcoder_abc301_f_G_1.py']
    files=[Path(__file__).resolve(),ROOT/'scripts/compare_s12_generic_operator.py',WORKER,PROOF]+sources+list(run.glob('*'))+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
    config=dict(run_id=run.name,image=read(PROOF)['image'],new_api_calls=0,case_policy='All three original statement samples, fixed before replay; boundary input is supplementary, not needed for triggering.',
        controls=[dict(kind='original',path=str(sources[0].relative_to(ROOT))),dict(kind='existing_manual_counterfactual',path=str(sources[1].relative_to(ROOT)))]+[dict(kind='archived_generic_model_repair',path=str(p.relative_to(ROOT))) for p in sources[2:]],
        budget=dict(max_calls=0,max_tokens=0,max_tools=80,max_cost_microusd=0,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=800000,tool_milliseconds_upper=10000,wall_seconds=900),
        frozen_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))})
    config['protocol_hash']=fingerprint(config);write(run/'protocol.json',config)


def execute(run):
    config=read(run/'protocol.json');assert config['protocol_hash']==fingerprint({k:v for k,v in config.items() if k!='protocol_hash'})
    for p,h in config['frozen_files'].items():assert sha(ROOT/p)==h
    if (run/'budget.jsonl').exists():raise FileExistsError('fresh replay run required')
    budget=PersistentBudget(run/'budget.jsonl',run_id=run.name,protocol_hash=config['protocol_hash'],**config['budget'])
    ev=CheckpointEvaluator(ROOT,budget,image=config['image'],worker_script=WORKER,acceptance_path=PROOF)
    cases=read(run/'statement_cases.json');task=read(run/'task_public.json');source=(CF/'original.py').read_text()
    evaluations=[]
    def judge(rawtask,code):
        observed=[]
        with tempfile.TemporaryDirectory(prefix='capacity-public-') as tmp:
            path=Path(tmp)/'program.py';path.write_text(code)
            for c in cases:
                def call():
                    with ev.factory(path) as worker:
                        compiled=worker.call(dict(mode='compile_stdio',timeout=3))
                        return worker.call(dict(mode='stdio',input=c['input'],timeout=3)) if compiled.get('status')=='OK' else compiled
                raw=ev._charged('public-program',call)
                correct=raw.get('status')=='OK' and compare_output(raw.get('output'),c['expected'],c['comparison'])
                match=re.search(r'(?m)^([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception)):',raw.get('stderr',''))
                exception_class=match.group(1) if match else None
                observed.append(dict(case=c,raw=raw,correct=correct,exception_class=exception_class))
        runtime=any(x['raw'].get('status')=='RUNTIME_ERROR' for x in observed)
        infrastructure=any(x['raw'].get('status') in ('EVALUATOR_ERROR','WORKER_ERROR','TIME_LIMIT') for x in observed)
        status='EVALUATOR_ERROR' if infrastructure else ('RUNTIME_ERROR' if runtime else ('PUBLIC_PASS' if all(x['correct'] for x in observed) else 'WRONG_ANSWER'))
        feedback=dict(visibility='public',status=status,tests_run=len(observed),tests_passed=sum(x['correct'] for x in observed),
            cases=[dict(visibility='public',legal_verified=True,input=x['case']['input'],expected=x['case']['expected'],actual=x['raw'].get('output',''),exception_class=x['exception_class']) for x in observed])
        evaluations.append(dict(code_sha256=hashlib.sha256(code.encode()).hexdigest(),cases=observed,feedback=feedback));return feedback
    # Replay only historical l1. No later generated candidate enters this checkpoint.
    facts=FailureEvidenceStore(run/'failure_facts.jsonl');registry=FailureOperatorRegistry(run/'empty_registry.jsonl',facts)
    context=Fingerprint('public-feedback-adapted-v2','isolated-statement-samples','historical-replay-stub',config['protocol_hash'],'capacity-headroom')
    checkpoints=[]
    class Recorder(FailureLearningPlugin):
        def invoke(self,hook,checkpoint,stage,code,feedback,budget,evaluator,at):
            checkpoints.append(dict(hook=hook,checkpoint_id=checkpoint,stage=stage,code_sha256=hashlib.sha256(code.encode()).hexdigest(),public_feedback=feedback.to_dict(),candidate_ledger=copy.deepcopy(self.current['ledger']),task_public=self.current['task'].to_dict()))
            return super().invoke(hook,checkpoint,stage,code,feedback,budget,evaluator,at)
    plugin=Recorder(registry,facts,context,stream_id=run.name,synthetic=False)
    replay_calls=[]
    def replay(request):
        assert request['stage']=='l1';replay_calls.append('historical-l1-not-an-API-call')
        return dict(code=source,model=context.model,usage={'total_tokens':0},finish_reason='stop')
    workflow=Controller(replay,judge,context,plugin=plugin).solve(task,Budget(max_calls=1,max_tokens=100000,wall_seconds=120))
    # Synthetic replay budget prevents generating l2a after the actual hook is observed.
    event=next((e for e in facts.visible(time.time()) if e['stage']=='l1'),None)
    gate=any(c['hook']=='before_native_retry' and c['stage']=='l2a' and c['public_feedback']['status']=='RUNTIME_ERROR' for c in checkpoints)
    primary=evaluations[0]
    boundary=read(run/'boundary_case.json');controls=[]
    for c in config['controls']:
        program=(ROOT/c['path']).read_text()
        controls.append(dict(**c,sha256=hashlib.sha256(program.encode()).hexdigest(),statement=ev.judge(program,cases,3),boundary=ev.judge(program,[boundary],3)))
    checkpoint=checkpoints[0] if checkpoints else None
    generic_action=generic(dict(candidate_code=source,candidate_ledger=checkpoint['candidate_ledger'])) if checkpoint else None
    # Produce a reviewable source-only discovery packet, not an Operator or paid Run.
    packet=dict(job_id=fingerprint([run.name,'capacity']),stream_id=run.name,family_id='bounded_index_capacity_repair',source_mode='historical_development',
        evidence_ids=[event['event_id']] if event else [],public_evidence=[event] if event else [],host_contract=build_compiler_contract(),
        task_public=task,candidate_code=source,public_feedback=checkpoint['public_feedback'] if checkpoint else {},
        allowed_action='candidate_code: bounded deterministic change to provably insufficient capacity and dependent initialization loops; no model calls inside Operator',
        limitations='No new Operator has been generated. Existing manual/G repaired sources are controls only and excluded from this packet. Same-task old tests are not independent Gate.')
    write(run/'discovery_packet.json',packet)
    result=dict(status='REACHABLE' if gate and event else 'BLOCKED',public_sample_replay=primary,workflow=workflow,observed_hooks=checkpoints,
        failure_fact=event,controls=controls,deterministic_retention_generic_action=generic_action,
        new_model_calls=0,new_operator_sources=0,natural_failure_provenance='real historical l1 code; current public workflow replay, not a new live model generation',
        strong_generic_already_covers=all(c['statement']['outcome']=='passed' and c['boundary']['outcome']=='passed' for c in controls if c['kind']=='archived_generic_model_repair'),
        generation_decision=generation_decision(reachable=gate, trusted_failure=bool(event)),budget=budget.snapshot())
    write(run/'result.json',result);print(json.dumps({k:result[k] for k in ['status','strong_generic_already_covers','generation_decision','new_model_calls']},indent=2))


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args();r=ROOT/a.run
    prepare(r) if a.prepare else execute(r)
if __name__=='__main__':main()
