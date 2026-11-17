"""Zero API: replay exposed episode 33; no model transport or independent game."""
import argparse
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from alfworld_.success_baseline import solve,BaselineClient,StrictTrainEnv
from alfworld_.skill_library import SkillLibrary
from alfworld_.route_b_runtime import RecoveryBridge
from alfworld_.learning_runtime import PolicyGenerator
from alfworld_.failure_learning import EnvironmentPolicyRunner,static_check
from failure_evo.contracts import fingerprint,canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read,sha,budget as tool_budget
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from test_alfworld_failure_learning import EnvironmentLearningTests
from run_alfworld_audited_baseline import budget
from run_alfworld_skill_acquisition import IMAGE,WORKER
from run_alfworld_a4_confirmatory import commit

SOURCE=Path.home()/'.local/share/flowevo/alfworld_full_library_online120_20261109_01'

def accept(out):
    out.mkdir(mode=0o700,parents=True,exist_ok=True)
    cfg=read(SOURCE/'protocol.json');row=cfg['tasks'][32]
    commits=[r['payload'] for r in EvidenceStore(SOURCE/'episodes.jsonl').records()]
    old=EvidenceStore(SOURCE/'episodes'/row['task_id']/'action/requests.jsonl').records()
    wires=[r['payload']['wire'] for r in old if r['kind']=='ACTION_REQUEST']
    responses=[r['payload']['response'] for r in old if r['kind']=='RAW_RESPONSE']
    expected_env=[r['payload'] for r in EvidenceStore(SOURCE/'episodes'/row['task_id']/'environment.jsonl').records()]
    fixtures={
      'declined':"def environment_operator(c):\n return {'status':'declined','state':{},'reason':'ENGINEERING_FIXTURE'}\n",
      'invalid_action':"def environment_operator(c):\n return {'status':'applied','action':'not an admissible action','state':{},'reason':'ENGINEERING_FIXTURE'}\n"}
    summaries={};baseline=None
    for mode in ('native','no_permission','declined','invalid_action'):
        root=out/mode;root.mkdir(exist_ok=True)
        conf=dict(cfg,run_id='route-b-b0:'+mode,max_calls=10,max_cost_microusd=1000000)
        account=budget(root,conf,engineering=True);sent=[]
        def sender(w):
            index=len(sent)
            assert canonical(w)==canonical(wires[index]),'native request changed'
            sent.append(fingerprint(w));return responses[index]
        client=BaselineClient(root/'action',account,conf,sender=sender,request_prefix='action/')
        factory=None;runner=None
        if mode!='native':
            card=None
            if mode in fixtures:
                code=fixtures[mode];assert static_check(code)['passed']
                artifact=root/'fixture.py';artifact.write_text(code)
                base=EnvironmentLearningTests().card()
                card=replace(base,version=fingerprint(code),artifact_path=str(artifact.resolve()),artifact_sha256=sha(artifact),
                    evidence_fingerprint=replace(base.evidence_fingerprint,model='MOCK'))
                runner=EnvironmentPolicyRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),root/'worker.jsonl',
                    tool_budget(root/'tools.jsonl','engineering:route-b-'+mode,'b0',calls=0,tools=4))
            registry=SimpleNamespace(evidence=SimpleNamespace(visible=lambda _:[]))
            def factory(native):
                return RecoveryBridge(PolicyGenerator(native,registry,runner,stream_id='engineering:b0',
                    experiment_id='NO_PERMISSIONS',task_id=row['task_id'],sequence=33,
                    events=EvidenceStore(root/'policy.jsonl'),engineering=True,validation_card=card))
        def execute():
            library=SkillLibrary.from_dict(commits[31]['library']);library.advance_episode()
            before=fingerprint(library.to_dict())
            value=solve(root,conf,row,library,commits[32]['holdout'],client,StrictTrainEnv,recovery_factory=factory)
            assert fingerprint(library.to_dict())==before,'current game changed skill bank'
            normalized=dict(value);normalized.pop('recovery_usage',None)
            normalized['trace']=dict(normalized['trace']);normalized['trace'].pop('trace_id',None)
            env=[r['payload'] for r in EvidenceStore(root/'environment.jsonl').records()]
            assert env==expected_env,'environment not equal to original exposed trajectory'
            return value,normalized
        value,normal=execute()
        if baseline is None:baseline=normal
        assert normal==baseline,'native outcome/skills/accounting changed'
        before_budget=sha(root/'budget.jsonl');before_tools=sha(root/'tools.jsonl') if runner else None
        sends=len(sent)
        client.sender=lambda _:(_ for _ in ()).throw(AssertionError('settled request resent'))
        again,normalized=execute()
        assert normalized==normal and len(sent)==sends
        assert sha(root/'budget.jsonl')==before_budget,'duplicate charge'
        if runner:assert sha(root/'tools.jsonl')==before_tools,'duplicate Worker charge'
        summary=dict(status='PASS',source_sequence=33,paid_requests=0,mocked_historical_responses=sends,
            environment_steps=value['trace']['total_steps'],environment_replayed_twice=True,
            trace_sha256=fingerprint(normal),use=value['use'],won=value['trace']['success'],
            recovery_usage=value.get('recovery_usage'),model_ledger_sha256=before_budget,
            worker_calls=runner.budget.tool_calls if runner else 0,worker_ledger_sha256=before_tools)
        summaries[mode]=summary;commit(root/'acceptance.json',summary)
    result=dict(status='PASS',scope='ENGINEERING_EXPOSED_GAME_ONLY',paid_requests=0,modes=summaries,
        independent_games_run=0,learned_candidates=0,fixture_algorithms_are_not_research_results=True)
    return commit(out/'Fallback_Acceptance.json',result)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(canonical(accept(a.output.resolve())))
