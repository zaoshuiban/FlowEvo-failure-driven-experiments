import pathlib,sys,json,time,tempfile,hashlib,requests,ast
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker,restore_budget
from failure_evo.contracts import fingerprint
from failure_evo.workflow_protocol_v2 import delivery
from experiment_s16b2_source import sender_factory
D=R/'reports/s20_gmp_attribution_v2';P=R/'runs/s20_gmp_strict5_20261026_02';B=R/'runs/s20_preparation_20261025_01';assert not P.exists()
for f,h in e.read(D/'freeze_hashes.json').items():assert e.sha(D/f)==h
pack=[x for x in e.read(D/'candidate_packets.json') if not x['task_id'].endswith('r2049')];wires=e.read(D/'frozen_wires.json');assert len(pack)==5 and len(wires)==15
for w in wires:assert e.prepare(w['messages']).sha256==w['wire_sha256']
quote=requests.get('https://api-docs.deepseek.com/quick_start/pricing/',timeout=30);quote.raise_for_status();assert '$0.3' in quote.text and '$1.2' in quote.text
cfg=e.prior.config(15,1600,15*40960);cfg['max_cost_microusd']=1000000
files=[pathlib.Path(__file__),pathlib.Path(__file__).with_name('evaluate.py'),R/'scripts/run_workflow_v2.py',R/'scripts/experiment_s16b2_source.py',R/'FlowEvo/src/failure_evo/workflow_protocol_v2.py',R/'FlowEvo/src/failure_evo/persistent_budget.py',D/'generic_advice.txt',D/'frozen_wires.json']
plan=dict(run_id=P.name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='real_experiment',frozen_files={str(f.relative_to(R)):e.sha(f) for f in files},budgets={'solve':cfg},tasks=[x['task_id'] for x in pack],excluded=dict(task='r2049',reason='all three arms failed identical input preflight before new model requests'),maximum_model_requests=15,hard_usd=1.0,per_branch_calls=1,worker_environment=e.read(B/'plan_G.json')['worker_environment'],source_protocol=e.sha(D/'protocol.json'),memory_sha256=e.read(D/'protocol.json')['memory_raw_sha256'],generic_sha256=e.sha(D/'generic_advice.txt'),request_hashes=[w['wire_sha256'] for w in wires],parameter_scope='fixed original wires; temperature0 output8192; no memory updates; empty identical success libraries; original remaining task and arm order',decision_point='Funding GO only when M-only vs P >=2 AND M-P net>0 AND M-G net>0 AND construction-inclusive M cost per joint success <=1.25x G. If G=0 or M=0 cost ratio is UNDEFINED and funding threshold not established; no infinity shortcut. Failure to meet is funding NO-GO, not scientific disproof. Infrastructure/token mismatch is INCOMPLETE. No automatic extension.',scoring='public AND same-task sealed all pass; held-out evaluation only after online lock; development, not blind independent confirmation',stopping=['UNKNOWN','worker failure','data contamination','budget exhausted','hash mismatch','M/P provider input tokens differ'],old_run_untouched=True,confirmation_pool_used=False,F_enabled=False)
plan['protocol_hash']=fingerprint(plan);configure_worker(plan['worker_environment']);r=e.ExperimentRunner(P,plan,sender_factory);(P/'tmp').mkdir();tempfile.tempdir=str(P/'tmp')
e.write(P/'authorization.json',dict(run_id=P.name,protocol_hash=plan['protocol_hash'],hard_usd=1,max_requests=15,basis='Standing user authorization for small real API validation; current instruction for a new five-task strict comparison; no old budget transferred'))
e.write(P/'packets.json',pack);e.write(P/'frozen_wires.json',wires);(P/'pricing.html').write_text(quote.text);out=[];tokens={}
try:
 # Worker preflight uses trusted fixture, no model call.
 fixture=r.judge.run('strict5_worker_fixture','print(2)',[dict(input='',expected='2',comparison='tokens',scorer='s1',visibility='public',legal_verified=True)])
 assert fixture['passed'];e.write(P/'worker_preflight.json',fixture)
 for w in wires:
  q=next(x for x in pack if x['task_id']==w['task_id']);res=r.transports['solve'].send(e.prepare(w['messages']),request_id=f"{w['arm']}/{w['task_id']}/repair1",capability='strict-GMP-repair',task_budget=restore_budget(q['checkpoint_budget']));d=delivery(res['text'],res['finish_reason']);code=d['code'];result=r.judge.run(q['task_id'],code,q['public_cases'])
  try:ast.parse(code);syntax=bool(code.strip())
  except SyntaxError:syntax=False
  out.append(dict(task_id=q['task_id'],arm=w['arm'],response=res,code=code,code_sha256=hashlib.sha256(code.encode()).hexdigest(),public_result=result,delivery=d,syntax_valid=syntax,request_sha256=w['wire_sha256']));e.write(P/'branches.json',out);r.save();print(q['task_id'],w['arm'],result['tests_passed'],result['tests_run'],flush=True)
  t=tokens.setdefault(q['task_id'],{});t[w['arm']]=res['usage']['prompt_tokens'];e.write(P/'provider_token_check.json',tokens)
  if 'M' in t and 'P' in t:assert t['M']==t['P'],'PROVIDER_TOKEN_MISMATCH'
 e.write(P/'online_lock.json',dict(locked=True,branches=15,branches_sha256=e.sha(P/'branches.json'),at=time.time()))
except Exception as exc:
 e.write(P/'stop.json',dict(status='INCOMPLETE',error=type(exc).__name__,reason=str(exc),completed=len(out)));raise
finally:r.save()
