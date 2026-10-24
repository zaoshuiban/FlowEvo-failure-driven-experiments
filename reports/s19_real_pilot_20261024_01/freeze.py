import sys,json,subprocess,shutil,platform,datetime,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.contracts import strict_stream_task,fingerprint
OUT=Path(__file__).parent
assert not (ROOT/'runs/s19_real_pilot_20261024_01').exists()
p=e.read(ROOT/'reports/s19_v2_acceptance/pilot_plan_proposal.json')
assert all(e.sha(ROOT/f)==h for f,h in p['frozen_files'].items())
source=ROOT/'runs/s19_pilot_preparation_20261024_04/pilot_tasks.json'
assert e.sha(source)==p['tasks_sha256']
tasks=[strict_stream_task(t) for t in e.read(source)];assert len(tasks)==10
shutil.copyfile(source,OUT/'tasks.json')
configure_worker(p['worker_environment']);(OUT/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(OUT/'tmp')
b=e.PersistentBudget(OUT/'worker_probe_budget.jsonl',run_id=OUT.name,protocol_hash=fingerprint(p),**e.prior.config(0,30,0))
j=e.prior.Judge(b)
cases=[dict(input='17\n',expected='17',comparison='tokens',scorer='s1')]
checks={'positive':j.run('engineering-identity','print(int(input()))',cases),'negative':j.run('engineering-identity','print(0)',cases)}
assert checks['positive']['passed'] and not checks['negative']['passed']
e.write(OUT/'worker_probe.json',dict(checks=checks,budget=b.snapshot(),real_model_api_calls=0))
image=subprocess.check_output(['docker','image','inspect',e.prior.old.IMAGE],text=True);(OUT/'worker_image.json').write_text(image)
requirements=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True);(OUT/'python_requirements.txt').write_text(requirements)
quote=dict(url='https://api-docs.deepseek.com/quick_start/pricing/',checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model='deepseek-flash',advertised_version='DeepSeek-V4.1-Flash-1017',units='USD per million tokens',peak=dict(cache_hit=.006,cache_miss=.30,output=1.20),off_peak=dict(cache_hit=.003,cache_miss=.15,output=.60),peak_windows_utc='Mon-Fri 01:00-04:00,06:00-10:00 excluding Chinese public holidays; weekends off-peak',invoice_available=False)
e.write(OUT/'price_quote.json',quote)
p.update(run_id='s19_real_pilot_20261024_01',git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),price_quote=quote,pricing_basis='Verified peak output rate bounds all tokens at 1.20 USD/million; full conservative reservation 2.850816 USD; cash cap 3.50 USD',preparation_status='AUTHORIZED_BY_CURRENT_USER_INSTRUCTION',authorization_basis='Current user explicitly requested this ten-task F-only Pilot and directed execution without another authorization question. Scope fixed to the existing 3.50 USD ceiling; no extension or old balance.',runtime_environment=dict(python=platform.python_version(),executable=sys.executable,platform=platform.platform()),max_total_requests=58,max_total_cash_usd=3.5)
# Add all repository Python sources and actually imported project dependencies.
for f in sorted((ROOT/'FlowEvo/src').rglob('*.py')):p['frozen_files'][str(f.relative_to(ROOT))]=e.sha(f)
for module in list(sys.modules.values()):
 f=Path(getattr(module,'__file__','') or '.')
 if f.is_file() and f.suffix=='.py' and ('/lab/' in str(f.resolve())) and '/.venv/' not in str(f.resolve()):
  f=f.resolve();key=str(f.relative_to(ROOT)) if ROOT in f.parents else str(f);p['frozen_files'][key]=e.sha(f)
for f in [Path(__file__),OUT/'tasks.json',OUT/'price_quote.json',OUT/'worker_image.json',OUT/'python_requirements.txt',ROOT/'reports/s19_v2_acceptance/pilot_public_acceptance.json',ROOT/'reports/s19_v2_acceptance/legacy_registry_diagnosis.json',ROOT/'reports/s19_v2_acceptance/legacy_baseline_hash_differences.json']:
 p['frozen_files'][str(f.relative_to(ROOT))]=e.sha(f)
p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
e.write(OUT/'plan.json',p)
auth=dict(run_id=p['run_id'],protocol_hash=p['protocol_hash'],model=p['model'],budgets=p['budgets'],allow_real_api=True)
e.write(OUT/'authorization.json',auth)
e.write(OUT/'authorization_record.json',dict(protocol_hash=p['protocol_hash'],max_cash_usd=3.5,task_sha256=p['tasks_sha256'],basis=p['authorization_basis'],scope='10 previously exposed development tasks, F only; no 40-task expansion or S20/S21',authorized_from='current user message',delegated_plan_freeze=True))
print(json.dumps(dict(run_id=p['run_id'],protocol_hash=p['protocol_hash'],files=len(p['frozen_files']),worker_passed=True,cash_cap_usd=3.5),indent=2))
