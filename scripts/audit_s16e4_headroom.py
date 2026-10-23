"""Bounded zero-API E4 audit. No generated code execution or registry changes."""
import json,hashlib,socket,urllib.request,time
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import run_workflow_v2 as e
from failure_evo.workflow_policy import validate_decision,CONTRACT
from failure_evo.workflow_runtime_v2 import PreparedController
from failure_evo.contracts import PublicTaskView,PublicFeedback,Fingerprint
from failure_evo.runtime import Budget
ROOT=e.ROOT;OUT=ROOT/'runs/s16e4_headroom_20261022_01';read=e.read;write=e.write;sha=e.sha
FILES=[
('repeated_truncation','runs/s16c2_reuse_20261022_01/taco_0914/G_workflow.json'),
('source_WA_replay','runs/s16e_workflow_20261022_03/public_discrepancy_policy/v0/functional.json'),
('source_runtime_replay','runs/s16e_workflow_20261022_03/runtime_fragment_policy/v0/functional.json'),
('preflight_stop','runs/s16c_reuse_20261022_02/M_workflow.json'),
('public_pass_control','runs/s15_learn_reuse30_20261022_01/branches/taco_0118/G/workflow.json'),
('extraction_control','runs/s16e_workflow_20261022_03/E1/taco_0533_verification.json')]

def audit():
 if OUT.exists():raise FileExistsError('preserve audit')
 watched={str(p):sha(p) for d in ('runs/s16c_reuse_20261022_02','runs/s16c2_reuse_20261022_01','runs/s16e_workflow_20261022_03','runs/s16b2_normalized_spec_20261022_01') for p in (ROOT/d).rglob('*') if p.is_file()}
 OUT.mkdir();write(OUT/'plan.json',dict(api_budget=0,selection='six predeclared records: four failure/blocked decision contexts plus two negative controls; no broad search or outcome-based replacement',files=[dict(label=k,path=p,sha256=sha(ROOT/p)) for k,p in FILES],claims='development observational audit; later public outcomes segregated, no hidden/external case data to candidate decisions',max_targets=1))
 rows=[]
 for kind,path in FILES:
  d=read(ROOT/path);row=dict(kind=kind,source=path,source_sha256=sha(ROOT/path))
  if kind in ('source_WA_replay','source_runtime_replay'):
   trials=d['trials'];row.update(prefix=dict(decision=trials[0]['decision'],public_result=trials[0]['public']['status'],first_code_hash=trials[0]['code_sha256']),retrospective_public=dict(statuses=[t['public']['status'] for t in trials],code_hashes=[t['code_sha256'] for t in trials]),native_generic_measured=False,independent_replays_not_sequential_controller=True,verdict='No native Generic paired evidence; changed code outputs, not proven duplicate execution. Algorithm/repair efficacy unresolved; cannot claim saved calls by stopping.')
  elif kind=='extraction_control':
   row.update(prefix=dict(reprojected_status=d['failure_public']['status'],tests_passed=d['failure_public']['tests_passed'],tests_run=d['failure_public']['tests_run']),verdict='Current shared extraction/public verification already yields PASS. Historical fragment runtime label is not current intervention headroom; no hidden result used.')
  else:
   ev=d['events'];first=ev[0];row['prefix']={k:first[k] for k in ('stage','code_sha256','public_feedback','budget') if k in first};row['retrospective_public']= [{k:z[k] for k in ('stage','code_sha256','public_feedback','error','request_state','diagnosis','budget') if k in z} for z in ev[1:]]
   row['later_outcomes_not_available_at_prefix']=True
   row['verdict']={'repeated_truncation':'G actually consumed two calls. After first failure a stop could avoid a second request in hindsight, but current policy cannot stop native retry and eventual success under another draw is unknown. Strong G also has same short-code requirement.','preflight_stop':'Existing shared preflight already refuses oversized retry before send. Strong G can enforce same bound; zero additional provider call to save. Compacting the request changes model input and requires future real paired validation.','public_pass_control':'Native workflow stops at first PUBLIC_PASS (one event), so no later candidate-loss opportunity in this trace.'}[kind]
  rows.append(row)
 write(OUT/'checkpoint_review.json',rows)
 # Actual controller with fixture provider/evaluator. No unknown code is executed.
 proofs=[];task=PublicTaskView.project(dict(problem_id='engineering-only',prompt='fixture'))
 for mode in ('generic','decline'):
  calls=[]
  def gen(payload,budget):calls.append(payload);return dict(code='print(1)',model='fixture')
  plugin=None
  if mode=='decline':
   class DecliningFixture:
    current=dict(ledger=[],hooks=[],snapshot=SimpleNamespace(snapshot_id='fixture'))
    def invoke(self,*args):return None
    def observe(self,*args,**kw):return dict(validation_cost={})
    def finish(self,*args):pass
   plugin=DecliningFixture()
  ctrl=PreparedController(gen,lambda *a:dict(status='PUBLIC_PASS',visibility='public',tests_run=1,tests_passed=1,cases=[]),Fingerprint('fixture','fixture','fixture','fixture','fixture'),plugin=plugin);ctrl.stages=(('l2a',0.),)
  result=ctrl._solve(task,Budget(max_calls=2),[],'',PublicFeedback('NO_COMPLETE_CODE'),None,plugin)
  proofs.append(dict(mode=mode,fake_provider_calls=len(calls),result=result['status'],generated_code_executed=False,real_api_calls=0))
 assert [p['fake_provider_calls'] for p in proofs]==[1,1]
 rejected=[]
 for action in ('stop','skip_retry','select_candidate','allocate_budget'):
  try:validate_decision(dict(status=action,reason='engineering fixture'))
  except ValueError:rejected.append(action)
 assert len(rejected)==4
 write(OUT/'decision_checks.json',dict(controller_fixture_comparison=proofs,unsupported_actions_rejected=rejected,decline_is_native_fallback_not_task_stop=True,scope='fixture demonstrates control flow only, not reliability/cost benefit'))
 target=dict(status='NO_GO_CURRENT_ACTION_SPACE',selected_learning_target=None,one_deferred_hypothesis='Bounded stop/continue choice after repeated truncation',why_not_selected=['stop/skip is unsupported by current frozen workflow contract','one failure does not prove next call valueless','no matched-reliability paired evidence; deterministic generic can implement same threshold','source replay failures are not natural repeated Generic attempts'],if_reopened=['separate host action protocol and safety/fallback review, not this audit','freeze prefix-only observations and identical strong-Generic stop rule','independent programs and actual paired full-cost outcomes, zero benefit credit for mere refusal'],generation_requests=0)
 write(OUT/'target_decision.json',target)
 changed=[p for p,h in watched.items() if sha(p)!=h];assert not changed
 write(OUT/'integrity.json',dict(historical_files_checked=len(watched),changed=changed,new_api_calls=0,operator_executions=0,registry_mutations=0))
 print(json.dumps(dict(checkpoints=len(rows),status=target['status'],new_api_calls=0,changed=changed)))
if __name__=='__main__':
 def deny(*a,**kw):raise AssertionError('S16-E4 zero API/network')
 with patch.object(urllib.request,'urlopen',side_effect=deny),patch.object(socket.socket,'connect',side_effect=deny),patch.object(e.prior,'configured_api_key',side_effect=deny):audit()
