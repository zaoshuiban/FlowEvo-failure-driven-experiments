"""Zero-provider isolated scoring checks; no candidate executes on the host."""
import os,json,hashlib,time,pathlib,tempfile,sys
import run_workflow_v2 as e
ROOT=e.ROOT;OUT=ROOT/'reports/s22_action_preference_v1'

def main():
 cfg=e.read(ROOT/'runs/s20_taco80_g_20261025_01/plan.json')['worker_environment']
 os.environ.update(DOCKER_HOST=cfg['docker_host'],DOCKER_CONFIG=cfg['docker_config'])
 # A new audit-only budget, never a historical ledger.
 from failure_evo.persistent_budget import PersistentBudget
 from failure_evo.contracts import fingerprint
 attempt=sys.argv[1] if len(sys.argv)>1 else '01'
 if attempt not in ('01','02','03'):raise ValueError('explicit audit attempt required')
 (OUT/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(OUT/'tmp')
 ledger=OUT/f'worker_budget_attempt{attempt}.jsonl'
 if ledger.exists():raise RuntimeError('Audit ledger already exists; do not silently rerun')
 b=PersistentBudget(ledger,run_id='s22-worker-zero-api',protocol_hash=fingerprint(cfg),**e.prior.config(0,1000,0))
 judge=e.prior.Judge(b);start=time.monotonic();rows=[]
 fixture=[dict(input='7\n',expected='7\n',scorer='s1',comparison='tokens')]
 for name,code in [('correct','print(int(input()))'),('wrong','print(0)'),('syntax','print('),('missing','')]:
  r=judge.run('s22-engineering',code,fixture);rows.append(dict(kind='engineering_fixture',name=name,passed=r['passed'],status=r['status']))
 assert rows[0]['passed'] and not any(x['passed'] for x in rows[1:])
 for path in sorted((OUT/'frozen').glob('*.json')):
  packet=e.read(path)['public_checkpoint'];r=judge.run(packet['task_id'],packet['code'],packet['public_cases'])
  rows.append(dict(kind='real_saved_source',task_id=packet['task_id'],checkpoint_sha256=fingerprint(packet),expected_status=packet['feedback']['status'],observed_status=r['status'],public_pass=r['passed'],tests_passed=r['tests_passed'],tests_run=r['tests_run'],status_matches=r['status']==packet['feedback']['status']))
  e.write(OUT/'worker_acceptance.json',dict(status='RUNNING',rows=rows,new_api_calls=0));print(packet['task_id'],r['status'],flush=True)
 acceptance=e.read(e.prior.old.ACCEPTANCE)
 manifest=dict(worker_environment=cfg,image=acceptance['image'],worker_script=str(e.prior.old.WORKER),worker_script_sha256=e.sha(e.prior.old.WORKER),judge_sha256=e.sha(ROOT/'scripts/learn_reuse30.py'),comparator_sha256=e.sha(ROOT/'scripts/compare30_workflows.py'),container_adapter_sha256=e.sha(ROOT/'FlowEvo/src/failure_evo/container_worker.py'))
 e.write(OUT/'worker_acceptance.json',dict(status='PASS' if all(x['status_matches'] and not x['public_pass'] for x in rows if x['kind']=='real_saved_source') else 'REVIEW_REQUIRED',rows=rows,new_api_calls=0,worker_manifest=manifest,wall_seconds=time.monotonic()-start,budget=b.snapshot(),scope='Source public failures reproduced; toy positives/negatives validate transport; no task gold programs or sealed tests read'))
if __name__=='__main__':main()
