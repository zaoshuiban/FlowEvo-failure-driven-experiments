"""Zero-API final artifact validation. Never instantiates a provider sender."""
import pathlib,sys,json,hashlib,math
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
from failure_evo.contracts import strict_stream_task,fingerprint
from failure_evo.workflow_protocol_v2 import prepare,Limits
T=e.read(P/'stream_tasks.json');H=e.read(P/'sealed_final_tasks.json');L=e.read(P/'task_lineage_manifest.json');prop=e.read(P/'long_stream_proposal.json');checks=[]
assert 60<=len(T)<=100;assert len(T)==len(H)==len(L);assert len({x['task_id'] for x in T})==len(T)
assert e.sha(P/'stream_tasks.json')==prop['tasks_sha256'];assert e.sha(P/'sealed_final_tasks.json')==prop['sealed_sha256']
for t,h,l in zip(T,H,L):
 strict_stream_task(t);assert t['task_id']==h['task_id']==l['task_id'];a={' '.join(c['input'].split()) for c in t['public_cases']};b={' '.join(c['input'].split()) for c in h['cases']};assert not a&b and len(b)==12
 assert len([x for x in t['public_cases'] if x['source']['kind']=='public_dataset'])==12
 assert len(l['reference_implementations'])==2
 for ref in l['reference_implementations']:assert e.sha(R/ref['path'])==ref['sha256']
checks.append({'name':'task_contract_roles_reference_hashes','passed':True,'tasks':len(T)})
solve=[];dollars=0;calls=0
for arm in ('G','M','F'):
 plan=e.read(P/f'plan_{arm}.json');assert plan['protocol_hash']==fingerprint({k:v for k,v in plan.items() if k!='protocol_hash'});assert plan['tasks_sha256']==e.sha(P/'stream_tasks.json');assert plan['arm']==arm
 for path,h in plan['frozen_files'].items():assert e.sha(R/path)==h
 solve.append(plan['per_task'])
 for channel,cfg in plan['budgets'].items():
  inputmax=65536 if arm=='M' and channel=='learning' else 32768
  assert cfg['max_tokens']==cfg['max_calls']*(inputmax+8192)
  assert cfg['max_cost_microusd']>=math.ceil(cfg['max_tokens']*1.2)
  dollars+=cfg['max_cost_microusd']/1e6;calls+=cfg['max_calls']
 assert not (P/f'authorization_{arm}.json').exists()
assert all(x==solve[0] for x in solve);assert dollars==prop['hard_budget_proposal_usd'];assert calls==prop['max_requests'];assert prop['authorized_usd']==0
checks.append({'name':'plan_hash_dependency_budget_units_fair_normal_limits','passed':True,'max_calls':calls,'max_usd':dollars})
worker=e.read(P/'worker_probes.json');assert worker['status']=='PASS' and len(worker['checks'])==12 and all(x['passed'] for x in worker['checks']);checks.append({'name':'real_worker_safety_probes','passed':True,'count':12})
p=e.read(P/'probe_preflight.json');assert p['status']=='AWAITING_NEW_EXPLICIT_AUTHORIZATION' and p['real_requests']==0;assert p['worst_case_reservation_usd']<=p['budget_proposal_usd']
checks.append({'name':'historical_probe_no_authorization','passed':True})
old=e.read(R/'reports/s19e_zero_api_replay_20261024_03/original_files_after.json');assert all(e.sha(R/'runs/s19_stream20_20261024_01'/k)==v for k,v in old.items());checks.append({'name':'historical_files_unchanged','passed':True,'count':len(old)})
e.write(P/'final_acceptance.json',{'passed':True,'checks':checks,'real_model_requests':0,'task_count':len(T),'online_cases':sum(len(t['public_cases']) for t in T),'sealed_cases':sum(len(t['cases']) for t in H),'authorized_usd':0});print(json.dumps(checks))
