"""Zero-model-API preflight. Creates an unsigned plan, never authorization."""
import sys,json,subprocess,shutil,tempfile,datetime,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.contracts import fingerprint,strict_stream_task
OUT=Path(__file__).parent
SOURCE=ROOT/'reports/s19_next_stream_20261024_03'
p=e.read(SOURCE/'plan_proposal.json');old_hash=p['protocol_hash']
assert fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})==old_hash
checks={f:e.sha(ROOT/f)==h for f,h in p['frozen_files'].items()};assert all(checks.values())
assert not subprocess.check_output(['git','diff','HEAD','--','FlowEvo','scripts'],cwd=ROOT)
tasks=[strict_stream_task(t) for t in e.read(SOURCE/'tasks.json')]
assert len(tasks)==20 and e.sha(SOURCE/'tasks.json')==p['tasks_sha256']
assert p['arm']=='F' and p['start_mode']=='cold' and p['batch_size']==5
assert p['compile_protocol']=='s19-compile-envelope-v2' and p['scheduler_protocol']=='evidence-diversity-v1'
assert not (ROOT/'runs/s19_stream20_20261024_01').exists()
shutil.copyfile(SOURCE/'tasks.json',OUT/'tasks.json');shutil.copyfile(SOURCE/'task_manifest.json',OUT/'task_manifest.json')
configure_worker(p['worker_environment']);(OUT/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(OUT/'tmp')
b=e.PersistentBudget(OUT/'probe_budget.jsonl',run_id=OUT.name,protocol_hash=old_hash,**e.prior.config(0,20,0))
j=e.prior.Judge(b);cases=[dict(input='19\n',expected='19',comparison='tokens',scorer='s1')]
probes={name:j.run('engineering-preflight',code,cases) for name,code in [('positive','print(int(input()))'),('negative','print(0)')]}
assert probes['positive']['passed'] and not probes['negative']['passed']
e.write(OUT/'worker_probe.json',dict(probes=probes,budget=b.snapshot(),real_api_calls=0))
image=json.loads(subprocess.check_output(['docker','image','inspect',e.prior.old.IMAGE],text=True))
prior=e.read(ROOT/'reports/s19_real_pilot_20261024_01/worker_image.json');assert image[0]['Id']==prior[0]['Id']
e.write(OUT/'worker_image.json',image)
(OUT/'python_requirements.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
quote=dict(url='https://api-docs.deepseek.com/quick_start/pricing/',checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model='deepseek-flash',advertised_version='DeepSeek-V4.1-Flash-1017',unit='USD per million tokens',peak=dict(cache_hit=.006,cache_miss=.30,output=1.20),off_peak=dict(cache_hit=.003,cache_miss=.15,output=.60),peak_windows_utc='Monday-Friday 01:00-04:00 and 06:00-10:00 except Chinese public holidays; weekends offpeak',actual_invoice_available=False)
e.write(OUT/'price_quote.json',quote)
budget_checks={}
for ch,c in p['budgets'].items():
 upper=c['max_tokens']*c['token_rate_microusd_per_million']/1e12
 assert upper<=c['max_cost_microusd']/1e6
 budget_checks[ch]=dict(calls=c['max_calls'],token_upper=c['max_tokens'],uniform_reserve_upper_usd=upper,cash_cap_usd=c['max_cost_microusd']/1e6)
assert sum(c['max_cost_microusd'] for c in p['budgets'].values())==8000000
p.update(run_id='s19_stream20_20261024_01',preparation_status='AWAITING_EXPLICIT_AUTHORIZATION',git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_proposal_hash=old_hash,price_quote=quote,
 pricing_basis='Official peak rate verified; uniform 1.20 USD/million reserve bounds all tokens; total 6.488064 USD <= separate cash caps totaling 8 USD',
 stopping='Only preregistered safety/protocol errors, unknown requests, data contamination, Worker failure or hard budget limits; no early stop for no successful Operator at task 5 or 10',
 runtime_environment=dict(python=platform.python_version(),executable=sys.executable,platform=platform.platform()))
for module in list(sys.modules.values()):
 f=Path(getattr(module,'__file__','') or '.')
 if f.is_file() and f.suffix=='.py' and '/lab/' in str(f.resolve()) and '/.venv/' not in str(f.resolve()):
  f=f.resolve();key=str(f.relative_to(ROOT)) if ROOT in f.parents else str(f);p['frozen_files'][key]=e.sha(f)
for f in (Path(__file__),OUT/'tasks.json',OUT/'task_manifest.json',OUT/'worker_probe.json',OUT/'worker_image.json',OUT/'python_requirements.txt',OUT/'price_quote.json'):
 p['frozen_files'][str(f.relative_to(ROOT))]=e.sha(f)
p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'});e.write(OUT/'plan.json',p)
e.write(OUT/'preflight.json',dict(passed=True,previous_dependencies_verified=len(checks),current_dependencies_frozen=len(p['frozen_files']),tasks=20,batches=4,cold=True,worker_image_id=image[0]['Id'],budgets=budget_checks,real_api_calls=0,authorization_status='NOT_GRANTED'))
assert not (OUT/'authorization.json').exists()
print(json.dumps(dict(protocol_hash=p['protocol_hash'],git_commit=p['git_commit'],task_sha256=p['tasks_sha256'],budget=budget_checks,worker_passed=True,real_api_calls=0),indent=2))
