import pathlib,sys,subprocess,requests,time
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];B=R/'runs/s20_preparation_20261025_01';sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.contracts import fingerprint
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='7229373535abc42794c9dd993d7f9f98308f8eda'
for f,h in e.read(B/'artifact_manifest.json').items():assert e.sha(B/f)==h,f
for f,h in e.read(B/'source_dependencies.json').items():assert e.sha(R/f)==h,f
assert e.read(B/'final_acceptance.json')['passed']
assert bool(e.prior.configured_api_key()),'API configuration missing'
quote=requests.get('https://api-docs.deepseek.com/quick_start/pricing/',timeout=30);quote.raise_for_status();(P/'pricing.html').write_bytes(quote.content)
assert all(x in quote.text for x in ('DeepSeek-V4.1-Flash-1017','$0.006','$0.3','$1.2'))
for a in 'GMF':
 p=e.read(B/f'plan_{a}.json');assert p['protocol_hash']==fingerprint({k:v for k,v in p.items() if k!='protocol_hash'});assert not (R/'runs'/p['run_id']).exists()
 configure_worker(p['worker_environment'])
 auth=dict(run_id=p['run_id'],protocol_hash=p['protocol_hash'],model=p['model'],budgets=p['budgets'],allow_real_api=True)
 e.write(P/f'authorization_{a}.json',auth)
e.write(P/'authorization_record.json',dict(user_message='授权',scope='S20-A frozen TACO80 G/M/F; 8 interleaved batches, 3 isolated persistent runs',authorized_usd=66,arm_caps_usd=dict(G=20,M=22,F=24),excluded=['external transfer','additional paid action pairing','S21','historical cross-task probe'],at=time.time(),commit='7229373535abc42794c9dd993d7f9f98308f8eda',plans={a:e.read(B/f'plan_{a}.json')['protocol_hash'] for a in 'GMF'},pricing_sha256=e.sha(P/'pricing.html')))
e.write(P/'preflight.json',dict(passed=True,at=time.time(),model_calls=0,credential_present=True,task_sha256=e.sha(B/'stream_tasks.json'),worker_config=e.read(B/'plan_G.json')['worker_environment'],historical_preparation_unchanged=True))
print('PREFLIGHT_PASS; fresh S20-A authorization recorded; no API request yet')
