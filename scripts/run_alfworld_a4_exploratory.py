"""Frozen offline A4: retention veto, then four-arm checkpoint comparison; zero API."""
import argparse,fcntl,time
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import run_alfworld_applicability_multicandidate as B
from audit_alfworld_a3b import card_for
from alfworld_.recovery_applicability_rule import check_rule
ROOT=B.ROOT
A3=ROOT/'runs/alfworld_route_a_a3b_semantic_feedback_20261114_01/pilot_frozen'
DATA=ROOT/'runs/alfworld_a4_checkpoints_20261115_02'
PREP=ROOT/'runs/alfworld_a4_preparation_20261115_01'
ARMS=['S0','S1','Rule','A3b_candidate_0']

def allows_recovery(arm,decision):
 if arm not in ARMS:raise ValueError('unknown arm')
 return arm=='S0' or decision['status']=='MATCH'

def prepare(out):
 if out.exists():raise FileExistsError(out)
 source=B.read(A3/'protocol.json');manifest=B.read(DATA/'checkpoint_manifest.json');freeze=B.read(PREP/'Candidate_Freeze.json')
 assert B.sha(DATA/'review.private.json')==manifest['review_sha256']
 samples=B.read(DATA/'review.private.json')['samples'];assert len(samples)==52 and all(s['role']=='INDEPENDENT_TEST' for s in samples)
 for x in freeze['arms'].values():assert B.sha(x['original_path'])==x['sha256']
 out.mkdir(parents=True,mode=0o700)
 files=[Path(__file__),Path(B.__file__),Path(B.pilot.__file__),ROOT/'scripts/audit_alfworld_a3b.py',ROOT/'scripts/run_alfworld_applicability_pilot.py',ROOT/'FlowEvo/src/alfworld_/recovery_applicability_rule.py',ROOT/'FlowEvo/src/alfworld_/recovery_applicability.py',ROOT/'FlowEvo/src/alfworld_/precondition_diagnostic.py',ROOT/'FlowEvo/src/alfworld_/failure_learning.py',ROOT/'FlowEvo/src/alfworld_/skill_acquisition.py']
 bound={str(p.resolve()):B.sha(p) for p in files}
 for p in [A3/'result.json',A3/'Final_Candidate_Freeze.json',DATA/'checkpoint_manifest.json',DATA/'review.private.json',DATA/'protocol.json',PREP/'Candidate_Freeze.json']:bound[str(p)]=B.sha(p)
 for s in samples:
  path=DATA/'games'/(s['source_key'].split('/')[0]+'.private.json');assert B.sha(path)==s['source_receipt_sha256'];bound[str(path)]=B.sha(path)
 plan=dict(source,version='a4-exploratory-v1',run_id='a4:'+out.name,scope='EXPLORATORY_CHECKPOINT_TRANSFER',max_calls=0,max_tokens=0,max_cost_microusd=0,
  worker_calls=4200,environment_steps=22000,source_window=18,episode_limit=50,wall_seconds=14400,arms=ARMS,
  files=bound,arms_frozen=freeze['arms'],selection='candidate_0 unchanged; retention failure stops without replacement',
  test_order='frozen review order, fixed S0/S1/Rule/A3b order, separate reset per executed branch',
  metrics='stratified per game/physical checkpoint; no full episode continuation; UNKNOWN false MATCH separate',
  Rule_execution='original trusted host check_rule; host time separate; recovery uses same Linux Worker',
  budgets_note='208x50+11x50 environmental base ceiling=10950; 22000 includes bounded prefix recovery. No unresolved-step retries.',
  paid_api_authorized=False)
 B.pilot.commit(out/'protocol.json',plan);return plan

def verify(out):
 p=B.read(out/'protocol.json')
 if p['version']!='a4-exploratory-v1' or p['max_calls'] or p['max_cost_microusd'] or p['arms']!=ARMS:raise PermissionError('protocol')
 for f,h in {**p['files'],**p['historical_sha256']}.items():
  if B.sha(f)!=h:raise PermissionError('frozen source/data changed: '+f)
 for x in p['arms_frozen'].values():
  if B.sha(x['original_path'])!=x['sha256']:raise PermissionError('candidate changed')
 backend=B.FrozenLinuxBackend(image=B.IMAGE,worker_script=B.WORKER)
 if backend.manifest()!=p['worker']:raise PermissionError('Worker drift')
 if B.pilot.environment_manifest(B.read(DATA/'protocol.json')['data_root'])!=p['environment']:raise PermissionError('environment drift')
 return p,backend

def setup(out,p,backend):
 budget=B.create_accounts(out,p);runner=B.EnvironmentPolicyRunner(backend,out/'worker.jsonl',budget)
 registry=B.FailureOperatorRegistry(out/'registry.jsonl',B.FailureEvidenceStore(out/'failures.jsonl'))
 receipts=B.pilot.EnvironmentReceipts(out/'environment.jsonl',p['environment_steps'])
 B.pilot.check_run(budget,SimpleNamespace(events=B.EvidenceStore(out/'provider.jsonl')),runner,None)
 roles=B.read(A3/'roles.private.json');known=B.register_source(out,registry,runner,roles,p)
 recovery=B.source_card(out,registry,p,known,'A4-frozen')
 gates={a:card_for(out,Path(p['arms_frozen'][a]['original_path']).read_text(),recovery,registry,a) for a in ['S1','A3b_candidate_0']}
 return budget,runner,registry,receipts,known,recovery,gates

def origin_for(s):
 path=DATA/'games'/(s['source_key'].split('/')[0]+'.private.json');g=B.read(path)
 if B.sha(path)!=s['source_receipt_sha256']:raise PermissionError('receipt changed')
 b=next(b for b in g['branches'] if b.get('branch')==s['source_key']);prefix=b['prefix']+[b['failure']]
 ids=s.get('public_history_scope',{}).get('retained_step_ids');visible=prefix if ids is None else [prefix[i-1] for i in ids]
 actual=B.pilot.context_view(g['origin']['goal'],prefix[-1]['observation'],prefix[-1]['commands'],visible,{})
 if {k:actual[k] for k in s['candidate_context']}!=s['candidate_context']:raise PermissionError('projection mismatch')
 origin=dict(g['origin'],steps=prefix+b['recovery_probe'],sequence=s['source_key'],projected={'anchor':len(prefix),'goal':g['origin']['goal']},receipt_sha256=B.sha(path))
 # Existing source validation is strictly train-only; all 52 labelled cases satisfy it.
 B.pilot.verify_source_game(B.read(DATA/'protocol.json')['data_root'],origin)
 return origin,ids

def run(out):
 p,backend=verify(out)
 with (out/'run.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  budget,runner,registry,receipts,known,recovery,gates=setup(out,p,backend)
  if (out/'result.json').exists():return B.read(out/'result.json')
  deadline=out/'start.json'
  if not deadline.exists():B.pilot.commit(deadline,dict(started=time.time(),protocol_sha256=B.fingerprint(p)))
  def timecheck():
   if time.time()-B.read(deadline)['started']>p['wall_seconds']:raise B.BudgetExhausted('frozen A4 wall budget')
  timecheck()
  rp=out/'exposed_regression.json'
  if not rp.exists():
   attempt={'version':gates['A3b_candidate_0'].version,'registration':{'card':gates['A3b_candidate_0'].to_dict()}}
   B.pilot.commit(rp,B.exposed_regression(p,out,attempt,runner,registry,receipts,known))
  regression=B.read(rp)
  if not regression['retention_passed']:
   return B.pilot.commit(out/'result.json',dict(status='RETENTION_VETO_A4_NOT_RUN',regression=regression,budget=budget.snapshot(),paid_requests=0))
  print('Retention passed: 11/11; beginning frozen A4 comparison',flush=True)
  rows=[];samples=B.read(DATA/'review.private.json')['samples']
  for i,s in enumerate(samples):
   origin,ids=origin_for(s)
   for arm in ARMS:
    timecheck();path=out/'outcomes'/arm/(B.fingerprint(s['sample_id'])+'.json')
    if path.exists():
     row=B.read(path)
     if row['sample_sha256']!=B.fingerprint(s):raise PermissionError('outcome changed')
     rows.append(row);continue
    ctx=dict(s['candidate_context'],state={});start=time.monotonic()
    if arm=='S0':decision=dict(status='UNGATED')
    elif arm=='Rule':decision=dict(status=check_rule(ctx))
    else:decision=B.learned_decision(runner,gates[arm],ctx)
    decision_seconds=time.monotonic()-start;live=None
    if allows_recovery(arm,decision):
     # Separate recovery identities ensure each arm executes its own environment branch.
     card=B.source_card(out,registry,p,known,arm+'/'+B.fingerprint(s['sample_id']))
     live=B.pilot.validate_source(p,B.read(DATA/'protocol.json')['data_root'],origin,B.fingerprint(s['sample_id']),card,runner,registry,receipts,out/'live'/arm,B.StrictTrainEnv,None,public_history_indices=ids)
    attempted=bool(live and live['first_action_executed'])
    row=dict(arm=arm,sample_id=s['sample_id'],sample_sha256=B.fingerprint(s),stratum=s['stratum'],game_sha256=s['game_sha256'],physical_state_group_id=s['physical_state_group_id'],expected=s['label'],decision=decision,decision_seconds=decision_seconds,live=live,actual_intervention=attempted,
     trusted_positive_repair=bool(s['label']=='MATCH' and live and live['local_repair_verified']),full_episode_benefit='NOT_EVALUATED_BOUNDED_RECOVERY_ONLY')
    B.pilot.commit(path,row);rows.append(row)
   print(f'A4 {i+1}/{len(samples)} checkpoint completed',flush=True)
  return B.pilot.commit(out/'result.json',dict(status='A4_EXPLORATORY_COMPLETED',protocol_sha256=B.fingerprint(p),regression=regression,rows=rows,budget=budget.snapshot(),paid_requests=0,published=False,full_episode_comparison=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('command',choices=['prepare','verify','run']);a.add_argument('--output',required=True,type=Path);args=a.parse_args()
 r=globals()[args.command](args.output.resolve());print(B.canonical({'command':args.command,'status':r.get('status','OK') if isinstance(r,dict) else 'OK'}))
