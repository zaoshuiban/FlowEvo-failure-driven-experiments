"""Read-only validation of S20 frozen inputs; writes only new S20 audit artifacts."""
import pathlib,sys,json,hashlib,collections
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
from failure_evo.contracts import strict_stream_task,fingerprint
old=R/'runs/s19g_train_expansion_20261024_01';checks=[]
for n in ('stream_tasks.json','sealed_final_tasks.json','task_lineage_manifest.json'):assert e.sha(P/n)==e.sha(old/n)
for scope in ('','external_'):
 ts=e.read(P/(scope+'public_tasks.json' if scope else 'stream_tasks.json'));hs=e.read(P/(scope+'sealed_tasks.json' if scope else 'sealed_final_tasks.json'))
 assert len(ts)==len(hs);assert len({t['task_id'] for t in ts})==len(ts)
 for t,h in zip(ts,hs):
  strict_stream_task(t);assert t['task_id']==h['task_id'];assert len(h['cases'])==12
  assert not {' '.join(x['input'].split()) for x in t['public_cases']}&{' '.join(x['input'].split()) for x in h['cases']}
 checks.append(dict(name=scope+'strict_public_and_disjoint_roles',count=len(ts),passed=True))
for a in 'GMF':
 p=e.read(P/f'plan_{a}.json');assert p['protocol_hash']==fingerprint({k:v for k,v in p.items() if k!='protocol_hash'});assert p['tasks_sha256']==e.sha(P/'stream_tasks.json')
 for f,h in p['frozen_files'].items():assert e.sha(R/f)==h,(f,'dependency mismatch')
 assert not (R/'runs'/p['run_id']).exists();assert not (P/f'authorization_{a}.json').exists()
checks.append(dict(name='three_new_unauthorized_plans_current_dependencies',passed=True))
for l in e.read(P/'external_lineage.json'):
 for r in l['references']:assert e.sha(R/r['path'])==r['sha256']
assert len({l['url'] for l in e.read(P/'external_lineage.json')})==60
w=e.read(P/'external_worker_results.json');assert len(w)==60 and all(x['passed'] and x['negative']['tests_passed']==0 and sum(r['result']['passed'] for r in x['references'])>=2 for x in w)
checks.append(dict(name='external_real_worker_60_two_references_negative',passed=True))
for f in ('worker_controller/acceptance.json','worker_batch_acceptance.json'):assert e.read(P/f)['passed']
assert e.read(P/'worker_probes.json')['status']=='PASS'
checks.append(dict(name='real_worker_controller_batch_pair_probes',passed=True))
for f,n in [('core_tests.log',212),('regression_final.log',28),('s20_tests_final.log',3)]:
 s=(P/f).read_text();assert f'Ran {n} tests' in s and '\nOK' in s
checks.append(dict(name='243_zero_api_unit_tests',passed=True))
prior=e.read(R/'reports/s19e_zero_api_replay_20261024_03/original_files_after.json')
for f,h in prior.items():assert e.sha(R/'runs/s19_stream20_20261024_01'/f)==h
checks.append(dict(name='old_stream159_files_unchanged',passed=True))
e.write(P/'final_acceptance.json',dict(passed=True,checks=checks,real_model_requests=0,authorized_usd=0,external_task_count=60,external_tool_calls=sum(r['budget']['tool_calls'] for r in w),external_charged_tool_seconds=sum(r['budget']['charged_or_reserved_tool_milliseconds'] for r in w)/1000,external_wall_seconds=e.read(P/'external_acceptance.json')['elapsed_seconds']))
manifest={str(f.relative_to(P)):e.sha(f) for f in P.rglob('*') if f.is_file() and not any(s in ('tmp','__pycache__') for s in f.parts) and f.suffix not in ('.lock','.pyc') and f.name!='artifact_manifest.json'}
e.write(P/'artifact_manifest.json',manifest);print(json.dumps(e.read(P/'final_acceptance.json'),indent=2))
