import pathlib,sys,json,time,tempfile,datetime,math,collections
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker
P=R/'runs/s20_gmp_pilot12_20261026_01';B=R/'runs/s20_preparation_20261025_01'
assert e.read(P/'online_lock.json')['locked'];assert e.sha(P/'branches.json')==e.read(P/'online_lock.json')['branches_sha256'];assert not (P/'sealed_results.json').exists(),'no implicit replay'
branches=e.read(P/'branches.json');assert len(branches)==36;plan=e.read(P/'plan.json');configure_worker(e.read(B/'plan_G.json')['worker_environment']);tempfile.tempdir=str(P/'tmp');budget=e.PersistentBudget(P/'solve_budget.jsonl',run_id=plan['run_id']+'-solve',protocol_hash=plan['protocol_hash'],**plan['budgets']['solve']);judge=e.prior.Judge(budget)
sealed={x['task_id']:x['cases'] for x in e.read(B/'sealed_final_tasks.json')};results=[];start=time.time()
for x in branches:
 y=judge.run(x['task_id'],x['code'],sealed[x['task_id']]);results.append(dict(task_id=x['task_id'],arm=x['arm'],result=y));e.write(P/'sealed_results.json',results)
def price(raw):
 u=raw['usage'];h=u.get('prompt_cache_hit_tokens',0);m=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-h);v=(h*.006+m*.3+u['completion_tokens']*1.2)/1e6;d=datetime.datetime.fromtimestamp(raw['created'],datetime.timezone.utc)
 return v if d.weekday()<5 and (1<=d.hour<4 or 6<=d.hour<10) else v/2
requests={x['request_id']:x for x in e.read(P/'solve_requests.json')};stats={};pairs=[]
for arm in 'GMP':
 xs=[x for x in branches if x['arm']==arm];ys=[x for x in results if x['arm']==arm];stats[arm]=dict(public_pass=sum(x['public_result']['passed'] for x in xs),sealed_pass=sum(y['result']['passed'] for y in ys),joint_pass=sum(x['public_result']['passed'] and next(y['result']['passed'] for y in ys if y['task_id']==x['task_id']) for x in xs),calls=len(xs),input_tokens=sum(x['response']['usage']['prompt_tokens'] for x in xs),output_tokens=sum(x['response']['usage']['completion_tokens'] for x in xs),tokens=sum(x['response']['usage']['total_tokens'] for x in xs),estimated_usd=sum(price(requests[f"{arm}/{x['task_id']}/repair1"]['raw_response']) for x in xs))
for tid in dict.fromkeys(x['task_id'] for x in branches):
 b={x['arm']:x for x in branches if x['task_id']==tid};s={x['arm']:x['result'] for x in results if x['task_id']==tid};pairs.append(dict(task_id=tid,arms={a:dict(public_pass=b[a]['public_result']['passed'],public_tests_passed=b[a]['public_result']['tests_passed'],sealed_pass=s[a]['passed'],sealed_tests_passed=s[a]['tests_passed'],joint=b[a]['public_result']['passed'] and s[a]['passed'],code_sha256=b[a]['code_sha256']) for a in 'GMP'},M_input_increment=b['M']['response']['usage']['prompt_tokens']-b['G']['response']['usage']['prompt_tokens'],P_input_increment=b['P']['response']['usage']['prompt_tokens']-b['G']['response']['usage']['prompt_tokens']))
contrasts={}
for a,b in [('M','G'),('M','P'),('P','G')]:
 w=sum(x['arms'][a]['joint'] and not x['arms'][b]['joint'] for x in pairs);l=sum(x['arms'][b]['joint'] and not x['arms'][a]['joint'] for x in pairs);n=w+l;pv=min(1,2*sum(math.comb(n,k) for k in range(min(w,l)+1))/2**n) if n else 1;contrasts[a+'-'+b]=dict(first_only=w,second_only=l,exact_mcnemar_p_unadjusted=pv)
src=R/'runs/s20_mechanism_acceptance_20261025_01';learn=[e.read(f) for f in src.glob('wire/learning/*/response.json') if int(f.parent.name)<=2];lc=sum(price(x) for x in learn);lt=sum(x['usage']['total_tokens'] for x in learn)
value=(stats['M']['estimated_usd']+lc)/stats['M']['joint_pass'] if stats['M']['joint_pass'] else None;gvalue=stats['G']['estimated_usd']/stats['G']['joint_pass'] if stats['G']['joint_pass'] else None
proceed=bool(contrasts['M-G']['first_only']>=3 and contrasts['M-P']['first_only']>contrasts['M-P']['second_only'] and value is not None and gvalue is not None and value<=1.25*gvalue)
summary=dict(stats=stats,contrasts=contrasts,pairs=pairs,learning_tokens=lt,learning_estimated_usd=lc,M_with_learning_estimated_usd=stats['M']['estimated_usd']+lc,decision='POSITIVE_EXPLORATORY_DIRECTION' if proceed else 'PAUSE_CURRENT_FIXED_MEMORY',decision_criteria=plan['decision_point'],M_cost_per_success_with_learning=value,G_cost_per_success=gvalue,neutral_matching='characters only, not token-exact',budget=budget.snapshot(),sealed_seconds=time.time()-start,new_evaluation_model_calls=0)
e.write(P/'summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k not in ['pairs','budget']},ensure_ascii=False))
