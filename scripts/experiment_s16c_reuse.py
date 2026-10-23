"""One frozen checkpoint G/M/F replay; original policy and live one-use authorization."""
import os,json,time,tempfile,random,copy
from pathlib import Path
import run_workflow_v2 as e
from experiment_s16b2_source import sender_factory
from failure_evo.contracts import fingerprint,canonical,PublicTaskView,PublicFeedback
from failure_evo.workflow_policy import WorkflowPolicy,WorkflowRegistry,WorkflowPlugin
from failure_evo.workflow_protocol_v2 import WorkflowClient,delivery
from failure_evo.workflow_runtime_v2 import PreparedController
from failure_evo.runtime import Budget
ROOT=e.ROOT;OLD=ROOT/'runs/s16b2_normalized_spec_20261022_01';OUT=ROOT/'runs/s16c_reuse_20261022_02';read=e.read;write=e.write;sha=e.sha

def oracle(a,moves):
    # Exact zero-sum minimax on suffixes, independent of any model/reference solution.
    dp=[0]*(len(a)+1)
    for i in range(len(a)-1,-1,-1):
        dp[i]=max(sum(1<<p for p in a[i:i+x])-dp[i+x] for x in moves if i+x<=len(a))
    return 'Chef' if dp[0]>0 else 'Garry' if dp[0]<0 else 'Draw'

def sealed_cases():
    rng=random.Random(160322);out=[]
    for n in range(1,9):
        for k in range(3):
            a=rng.sample(range(21),n);moves=sorted(set([1]+rng.sample(range(1,n+1),rng.randint(1,n))))
            out.append(dict(input=f'1\n{n} {len(moves)}\n'+ ' '.join(map(str,a))+'\n'+' '.join(map(str,moves))+'\n',expected=oracle(a,moves),comparison='tokens',scorer='s1',origin='new_engineering_legal_input_exact_minimax_not_independent_task'))
    return out

def main():
    packet=read(ROOT/'runs/s16b_preflight_20261022_02/sources/taco_0511/checkpoint.json');ev=packet['public_evidence']
    rawpath=ROOT/packet['lineage']['raw_response_path'];assert sha(rawpath)==packet['lineage']['raw_response_sha256']
    raw=read(rawpath)['choices'][0];assert delivery(raw['message']['content'],raw['finish_reason'])['code']==ev['candidate_code']==''
    assert raw['finish_reason']==ev['generation_metadata']['finish_reason']=='length'
    full=next(t for t in read(ROOT/'runs/s15_learn_reuse30_20261022_01/tasks.json') if t['task_id']=='taco_0511')
    task={k:full[k] for k in ('task_id','dataset','difficulty','task_public','public_cases','reference_path','reference_sha256')}
    assert task['task_public']==ev['task_public'] and sha(task['reference_path'])==task['reference_sha256']
    scope=read(OLD/'operators/v0/probation_scope.json');assert scope['task_ids']==['taco_0511'] and scope['maximum_opportunities']==1
    card=WorkflowPolicy.from_dict(read(OLD/'summary.json')['cards'][0]['card']);assert sha(card.artifact_path)==card.artifact_sha256
    memory=canonical(read(OLD/'normalized_specification.json'));assert len(memory)<=6000
    sealed=sealed_cases();assert oracle([0],[1])=='Chef' and oracle([0,5],[1])=='Garry'
    files=[Path(__file__),ROOT/'scripts/run_workflow_v2.py',ROOT/'scripts/experiment_s16b2_source.py',Path(card.artifact_path),OLD/'normalized_specification.json',OLD/'operators/v0/probation_scope.json',rawpath,Path(task['reference_path'])]+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
    plan=dict(run_id=OUT.name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='real_experiment',frozen_files={str(p.relative_to(ROOT)):sha(p) for p in files},budgets={'solve':e.prior.config(6,240,300000)},per_task=dict(max_calls=2,max_tokens=81920,max_tools=40,wall_seconds=240),source_packet_sha256=fingerprint(packet),public_cases_sha256=fingerprint(task['public_cases']),sealed_cases_sha256=fingerprint(sealed),memory_sha256=fingerprint(memory),order=['G','M','F'],new_generation_calls=0,hard_budget_usd=.30,price={'input_miss_per_million':.3,'output_per_million':1.2,'source':'https://api-docs.deepseek.com/quick_start/pricing/','checked':'2026-10-22'},request_limits={'input_upper':32768,'output':8192,'thinking':'disabled','temperature':0},quoted_full_bound_usd=.1179648,prior_learning_tokens=10532,prior_learning_estimate_usd=.0058893,local_currency_cost=None,scope=scope,authorization='User requested S16-C: one checkpoint G/M/F, two shared solve calls per arm, fresh $0.30 hard cap; no generation or policy changes.',checkpoint_interpretation='Historical naturally observed delivery failure; shared two-call replay cap, not full native run. G/M/F receive same projected checkpoint; M receives unchanged normalized source specification. Final held-back inputs never used for retries.',registry_context='Reuse original source authorization and evidence fingerprint for frozen policy; new request transport has new run/protocol hash. Exact source dependency hashes verified.')
    plan['protocol_hash']=fingerprint(plan)
    os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
    runner=e.ExperimentRunner(OUT,plan,sender_factory);(OUT/'tmp').mkdir();tempfile.tempdir=str(OUT/'tmp')
    write(OUT/'authorization.json',dict(run_id=OUT.name,protocol_hash=plan['protocol_hash'],budgets=plan['budgets'],allow_real_api=True,basis=plan['authorization']))
    write(OUT/'checkpoint.json',packet);write(OUT/'public_task.json',task);write(OUT/'held_back_cases.json',sealed);write(OUT/'M_memory.json',dict(memory=memory,origin='verbatim normalized historical real specification; no target adaptation'))
    registry=WorkflowRegistry(OLD/'registry.jsonl',e.FailureEvidenceStore(OLD/'evidence_F.jsonl'))
    review=registry.review(card);assert review['opportunities_used']==0 and review['permission']=='experimental'
    (OUT/'registry_before.jsonl').write_bytes((OLD/'registry.jsonl').read_bytes());write(OUT/'registry_review_before.json',review)
    results={};error=None
    try:
        # Reference is only an evaluator positive control, never solver input.
        ref=Path(task['reference_path']).read_text()
        checks=dict(public=runner.judge.run(task['task_id'],ref,task['public_cases']),held_back_reference=runner.judge.run(task['task_id'],ref,sealed),invalid=runner.judge.run(task['task_id'],"print('INVALID')",task['public_cases']))
        write(OUT/'scorer_acceptance.json',checks)
        assert checks['public']['passed'] and checks['held_back_reference']['passed'] and not checks['invalid']['passed'],'scorer/reference disagreement'
        for arm in plan['order']:
            start=time.monotonic();before=runner.budgets['solve'].snapshot();local=Budget(**plan['per_task'])
            client=WorkflowClient(runner.transports['solve'],arm+'/taco_0511',memory=memory if arm=='M' else '')
            # Same projected empty artifact/finish reason for all arms, not the old unfinished prose.
            client.last=dict(text='```python\n\n```',code='',finish_reason='length')
            plugin=None;context=runner.context
            if arm=='F':
                assert task['task_id'] in scope['task_ids'] and sha(card.artifact_path)==card.artifact_sha256
                context=card.evidence_fingerprint
                plugin=WorkflowPlugin(registry,runner.stores['F'],context,stream_id=scope['stream_id'],experiment_id=OLD.name,host_repair=client.host_repair,decision_runner=runner.judge.decision,synthetic=False)
                plugin.begin(PublicTaskView.project(ev['task_public']),time.time())
                assert any(c.artifact_sha256==card.artifact_sha256 for c in plugin.current['snapshot'].cards),'not authorized'
                plugin.observe('', 'l1',PublicFeedback.project(ev['public_feedback']),dict(finish_reason='length'),time.time(),learnable=False)
            controller=PreparedController(client,lambda public,code:runner.judge.run(task['task_id'],code,task['public_cases']),context,plugin=plugin)
            controller.stages=(('l2a',0.),('l2b',0.))
            result=controller._solve(PublicTaskView.project(ev['task_public']),local,[],ev['candidate_code'],PublicFeedback.project(ev['public_feedback']),None,plugin)
            after=runner.budgets['solve'].snapshot();result['measured_wall_seconds']=time.monotonic()-start
            result['tool_calls']=after['tool_calls']-before['tool_calls'];result['tool_milliseconds']=after['charged_or_reserved_tool_milliseconds']-before['charged_or_reserved_tool_milliseconds']
            results[arm]=result;write(OUT/f'{arm}_workflow.json',result);runner.save()
            print(arm,result['status'],'calls',local.calls,'tokens',local.used_tokens,flush=True)
            if any(row['status']=='UNKNOWN' for row in runner.transports['solve'].audit):raise RuntimeError('unknown request stops whole run')
        # All branches frozen before final same-task independent-oracle review; never feed this back.
        for arm,result in results.items():
            code=result['selected']['code'] if result['selected'] else result['last_candidate']
            review=runner.judge.run(task['task_id'],code,sealed);write(OUT/f'{arm}_held_back_review.json',review);result['held_back']=review
        f=results['F'];hooks=f.get('hook_events',[])
        if any(x.get('status')=='applied' for x in hooks) and not f['held_back']['passed']:
            registry.suspend(card,'S16-C public-accepted proposal fails frozen independent-oracle same-task review',time.time())
    except Exception as exc:
        error=dict(type=type(exc).__name__,message=str(exc));print('STOPPED',error,flush=True)
    finally:
        runner.save();rows=[x for x in runner.transports['solve'].audit if x.get('raw_response')]
        stats={}
        for arm,result in results.items():
            rr=[x for x in rows if x['request_id'].startswith(arm+'/')];usage=[x['raw_response']['usage'] for x in rr]
            stats[arm]=dict(public_pass=result['status']=='PUBLIC_ACCEPTED',held_back_pass=result.get('held_back',{}).get('passed'),calls=len(rr),tokens=sum(u['total_tokens'] for u in usage),estimated_usd=sum((u['prompt_tokens']*.3+u['completion_tokens']*1.2)/1e6 for u in usage),tool_calls=result['tool_calls'],tool_milliseconds=result['tool_milliseconds'],wall_seconds=result['measured_wall_seconds'],hooks=result.get('hook_events',[]))
        write(OUT/'summary.json',dict(error=error,arms=stats,registry=registry.review(card),budget=runner.budgets['solve'].snapshot(),policy_unchanged=sha(card.artifact_path)==card.artifact_sha256,actual_requests=len(rows),prior_build_tokens=10532,prior_build_estimated_usd=.0058893,independent_tasks=1,held_back_inputs=len(sealed),new_generation_calls=0))
        (OUT/'registry_after.jsonl').write_bytes((OLD/'registry.jsonl').read_bytes())
        print('COMPLETE', {a:{k:v for k,v in x.items() if k!='hooks'} for a,x in stats.items()},flush=True)
    if error:raise RuntimeError('inspect run; no automatic retry')
if __name__=='__main__':main()
