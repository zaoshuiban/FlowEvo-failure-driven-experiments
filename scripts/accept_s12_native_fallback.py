"""Supplemental real-controller fallback checks using a local generator stub, no API."""
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
from failure_evo.contracts import PublicFeedback, fingerprint
from failure_evo.failure_registry import FailureOperator
from failure_evo.plugin import FailureLearningPlugin
from failure_evo.runtime import Budget, Controller
from failure_evo.checkpoint_evaluator import CheckpointEvaluator
from accept_s12_operator import EvaluationOnlyRegistry, WORKER, SOURCE, write, sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--image',required=True);a=p.parse_args()
    parent=ROOT/a.run;out=parent/'native_fallback';out.mkdir(exist_ok=False)
    card=FailureOperator.from_dict(json.loads((SOURCE/'shadow_registry.jsonl').read_text().splitlines()[0])['payload']['card'])
    protocol=dict(scope='synthetic controller continuation; no natural online evidence',source_sha256=sha(Path(__file__)),artifact_sha256=sha(Path(card.artifact_path)),image=a.image)
    write(out/'protocol.json',protocol)
    budget=PersistentBudget(out/'budget.jsonl',run_id=parent.name+'-fallback',protocol_hash=fingerprint(protocol),max_calls=0,max_tokens=0,max_tools=30,max_cost_microusd=0,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=300000,tool_milliseconds_upper=10000,wall_seconds=300)
    evaluator=CheckpointEvaluator(ROOT,budget,image=a.image,worker_script=WORKER,acceptance_path=parent/'worker_acceptance.json')
    raw_context=json.loads((SOURCE/'generation_input.json').read_text())['runtime_context_example']
    old=evaluator._charged('historical-unavailable',lambda:evaluator.runner.run(card,raw_context,1))
    records=[]
    good='print(input())\n';cases=[dict(case_id='fallback-echo',input='7\n',expected='7\n',comparison='whitespace_token_exact')]
    public=evaluator.judge(good,cases,3);assert public['outcome']=='passed'
    for mode in ('budget_insufficient','worker_exception','host_checker_exception'):
        calls=[];checker_calls=[]
        class FixturePlugin(FailureLearningPlugin):
            def begin(self,task,at):
                self.current=dict(task=task,snapshot=SimpleNamespace(cards=(card,),snapshot_id='ENGINEERING_ONLY'),ledger=[],observations=[],hooks=[],attempted=set())
                self.observe(good,'l2a',PublicFeedback('PUBLIC_PASS'),{},at)
            def finish(self,at):pass  # No synthetic evidence publication.
        class Runner:
            def run(self,c,p,t):
                if mode=='worker_exception':raise RuntimeError('engineering worker outage')
                return evaluator._charged('controller-operator',lambda:evaluator.runner.run(c,p,t))
        plugin=FixturePlugin(EvaluationOnlyRegistry(),None,card.evidence_fingerprint,stream_id='fixture',synthetic=True,runner=Runner())
        def generator(request):
            calls.append(request['stage'])
            return dict(model=card.evidence_fingerprint.model,code='' if len(calls)==1 else good,usage={'total_tokens':0},finish_reason='stop')
        def judge(task,code):
            checker_calls.append(code)
            if mode=='host_checker_exception' and len(checker_calls)==1:raise RuntimeError('engineering host checker outage')
            v=evaluator.judge(code,cases,3)
            return dict(visibility='public',status='PUBLIC_PASS' if v['outcome']=='passed' else 'WRONG_ANSWER',tests_run=v['tests_run'],tests_passed=v['tests_passed'])
        controller=Controller(generator,judge,card.evidence_fingerprint,plugin=plugin)
        workflow=controller.solve(dict(problem_id='fixture-fallback-'+mode,prompt='Echo an integer.'),Budget(max_calls=2,max_tokens=100000,max_tools=2 if mode=='budget_insufficient' else 20,wall_seconds=30))
        passed=calls==['l1','l2a'] and workflow['status']=='PUBLIC_ACCEPTED' and workflow['selected']['code']==good
        records.append(dict(name=mode,passed=passed,synthetic_generator_stages=calls,actual_model_api_calls=0,workflow=workflow))
    result=dict(status='PASS' if old['status']=='declined' and all(r['passed'] for r in records) else 'FAIL',original_unverified_historical_action=old,controller_checks=records,budget=budget.snapshot(),real_model_calls=0,natural_online_evidence=False)
    write(out/'result.json',result);print(result['status'])
if __name__=='__main__':main()
