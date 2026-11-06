"""Real sealed-provider release A, then contract-only B; engineering, zero model API."""
import argparse,copy,json,time
from pathlib import Path
from types import SimpleNamespace
from accept_post_pilot50_validator import fixture
from run_math_manual_lifecycle import problem
from test_math_continuous_stream import solve_sender
from failure_evo.contracts import fingerprint
from failure_evo.math_stream import StreamRuntime,save,sha
from failure_evo.math_gate_pool import PoolReviewedRelease,review_version
from failure_evo.operator_contract import candidate_identity
from failure_evo.math_contract_runtime import validate_safety,ContractShadow
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from run_math_v3_development import IMAGE,WORKER

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--output',type=Path,default=Path.home()/'.local/share/flowevo/engineering_runs/sealed_version_cache_20261105_01')
 parser.add_argument('--automated',action='store_true')
 parser.add_argument('--wrong-gate',action='store_true')
 args=parser.parse_args()
 if args.wrong_gate and not args.automated:parser.error('--wrong-gate requires --automated')
 root=args.output
 if root.exists():raise RuntimeError('new engineering namespace required')
 root.mkdir(parents=True);root.chmod(0o700)
 tasks=[dict(task_id='s1',problem=problem(1)),dict(task_id='s2',problem=problem(2)),dict(task_id='negative',problem='Compute the product of integers from 1 through 3, inclusive.'),dict(task_id='future',problem=problem(9)),dict(task_id='trial',problem=problem(10))]
 values=['1','3','6','45','55'];private=[dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),gold_answer=v) for t,v in zip(tasks,values)]
 refs=root/'private_scores.jsonl';refs.write_text(''.join(json.dumps(r)+'\n' for r in private))
 lineage={t['task_id']:dict(source_original_id='source1' if i==0 else 'source2' if i==1 else 'original-'+t['task_id']) for i,t in enumerate(tasks)}
 pool=[dict(task_id='g'+str(i),original_id='MOCK_GATE_'+str(i),problem=problem(100+i) if i<2 else 'Compute the product of integers from 1 through 3, inclusive.',answer=str((100+i)*(101+i)//2) if i<2 else '6',oracle_sha256=fingerprint(['fixture',i])) for i in range(4)]
 a,_,_,_=fixture(root/'candidate');a.update(excluded_task_ids=['s1','s2'],candidate_created_after=3)
 labels=lambda tid,positive,parameters,q:dict(task_id=tid,supported=positive,parameters=parameters,reason='ENGINEERING_FIXTURE_REVIEW',assumption_quotes=[q])
 dev_labels=[labels(t['task_id'],i<2,{'n':i+1} if i<2 else None,t['problem']) for i,t in enumerate(tasks[:3])]
 gate_labels=[labels(t['task_id'],i<2,{'n':100+i} if i<2 else None,t['problem']) for i,t in enumerate(pool)]
 extra={}
 if args.automated:
  if args.wrong_gate:pool[0]['answer']='0'
  def hashed(rows):
   return [dict(row,problem_sha256=fingerprint(row['assumption_quotes'][0])) for row in rows]
  future_label=labels(tasks[3]['task_id'],True,{'n':9},tasks[3]['problem'])
  extra['automated_profiles']={fingerprint(a['contract']):dict(Development=hashed(dev_labels+[future_label]),Gate=hashed(gate_labels))}
 pp=root/'pool.json';save(pp,dict(origin='ENGINEERING_FIXTURE',cases=pool,**extra))
 plan=dict(tasks_sha256=fingerprint(tasks),window=2,r_policy='previous-window-f-call-credit-v1',r_max_extra_calls=27,max_gate_cases=6,max_tools_per_arm=500,gate_pool_binding=dict(path=str(pp),sha256=sha(pp)),gate_reviewers=['ENGINEERING_REVIEWER'],cumulative_input_bindings=dict(private_scoring=dict(path=str(refs),sha256=sha(refs))))
 if args.automated:plan.update(gate_mode='AUTOMATED_GATE',automatic_gate_validator='split-exact-rational-v1',operator_contract_shadow='pre-score-one-candidate-v1',stop_for_gate_review=False)
 def factory(s,arm):
  return SimpleNamespace(capacity=lambda *a,**k:True,_path=lambda cutoff,key:s.path/arm/'learning'/str(cutoff)/key)
 stream=StreamRuntime(root/'stream',plan,tasks,private,lineage,backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),learner_factory=factory,engineering=True,sender_factory=solve_sender)
 state=stream.arms['F']
 for seq,t in enumerate(stream.tasks[:3],1):
  lock=stream.solve('F',t,seq);verdict=state['scorer'].score(t,lock)
  stream.emit_once(state['states'],'PRIVATE_SCORED',t.task_id,dict(task_id=t.task_id,sequence=seq,verdict=verdict))
 state['registry'].shadow(a)
 release=PoolReviewedRelease(stream,'F');release.sender=solve_sender('F')
 if args.automated:
  assert release.attempt(a,3,root/'release')['status']=='UNVERIFIED_AUTOMATED_GATE_EVIDENCE'
  assert not state['split'].events.records()
 validate_safety(state['registry'],a,state['split'],engineering=True)
 if not args.automated:
  review=dict(version=review_version(a),candidate_version=candidate_identity(a),artifact_sha256=a['code_sha256'],pool_sha256=sha(pp),reviewer='ENGINEERING_REVIEWER',review_method='INDEPENDENT_SEMANTIC_REVIEW_BEFORE_EXECUTION',Development=dev_labels,Gate=gate_labels)
  save(release.packages.review_path(a),review)
 before=release.attempt(a,3,root/'release')
 if args.wrong_gate:
  assert before['status']=='BLOCKED_AUTOMATED_GATE_MATH_FAILED'
  assert release.attempt(a,3,root/'release')==before
  assert not any(r['kind'] in ('MATH_EXPERIMENTAL','V3_TRIAL_AUTHORIZATION') for r in state['registry'].events.records())
  assert not list(root.rglob('gate_budget.jsonl'))
  print(json.dumps(dict(automatic=True,wrong_answer_blocked=True,paid_model_calls=0)))
  return
 assert before['status']=='SHADOW_RELEASE_STAGES_PENDING'
 shadow=ContractShadow(stream,'F',private);task=stream.tasks[3];shadow.observe(task,4)
 lock=stream.solve('F',task,4);verdict=state['scorer'].score(task,lock)
 stream.emit_once(state['states'],'PRIVATE_SCORED',task.task_id,dict(task_id=task.task_id,sequence=4,verdict=verdict))
 shadow.finalize(task,lock)
 if args.automated:
  frozen=release.packages(a,4)
  assert [row['task_id'] for row in frozen['Development']]==['s1','s2','negative']
  assert all(row['available_after_sequence']==3 for row in frozen['Development']+frozen['Gate'])
 published=release.attempt(a,4,root/'release');assert published['status']=='EXPERIMENTAL'
 b=copy.deepcopy(a);b['operator_contract']['failure_modes'].append('new contract restriction');b['candidate_version']=__import__('failure_evo.operator_contract',fromlist=['binding']).binding(b)
 assert b['code_sha256']==a['code_sha256'] and candidate_identity(a)!=candidate_identity(b)
 worker_before=len(state['split'].events.records());result=release.attempt(b,4,root/'release-B')
 assert result['status']==('BLOCKED_AUTOMATED_GATE_POOL_CONSUMED' if args.automated else 'SHADOW_INDEPENDENT_REVIEW_UNAVAILABLE')
 assert len(state['split'].events.records())==worker_before
 assert release.packages.review_path(a)!=release.packages.review_path(b)
 assert [x['candidate_version'] for x in release.pending_records()]==([] if args.automated else [candidate_identity(b)])
 completed=[r for r in release.journal.records() if r['kind']=='RELEASE_COMPLETED']
 assert len(completed)==1 and completed[0]['payload']['candidate_version']==candidate_identity(a)
 checks=dict(actual_linux_worker=True,A_validated_and_published=True,same_code_hash=True,different_candidate_versions=True,B_requires_new_review=not args.automated,B_blocked_consumed_pool=args.automated,B_does_not_inherit_A_completion=True,B_no_worker_execution_before_review=True,paid_model_calls=0,engineering_only=True)
 save(root/'checks.json',checks);print(json.dumps(checks))
if __name__=='__main__':main()
