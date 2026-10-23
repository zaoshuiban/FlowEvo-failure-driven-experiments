"""Two preregistered chronological delivery failures; unchanged v0; no learning API."""
import json,os,time,tempfile,random,itertools,copy,sys
from pathlib import Path
import run_workflow_v2 as e
from experiment_s16b2_source import sender_factory
from s16c2_probation import RenewedRegistry
from failure_evo.contracts import fingerprint,canonical,PublicTaskView,PublicFeedback
from failure_evo.workflow_policy import WorkflowPolicy,worker_context,validate_decision
from failure_evo.workflow_protocol_v2 import WorkflowClient,delivery,Limits,prepare,repair_messages
from failure_evo.workflow_runtime_v2 import PreparedController
from failure_evo.runtime import Budget
ROOT=e.ROOT;OLD=ROOT/'runs/s16b2_normalized_spec_20261022_01';S15=ROOT/'runs/s15_learn_reuse30_20261022_01';C=ROOT/'runs/s16c_reuse_20261022_02';OUT=ROOT/'runs/s16c2_reuse_20261022_01'
read=e.read;write=e.write;sha=e.sha
MEMORY=('A previous failure delivered no program: empty code, NO_COMPLETE_CODE, length termination, and no executed public tests. '
'Treat this as an uncertified delivery failure, not an existing algorithm needing a wrapper. '
'When this condition holds before a native retry and budget covers one repair, public verification and fallback, request one complete, nonempty, parseable program. '
'Do not rely on unfinished prose as an algorithm or invent hidden evidence. Verify with public checks. '
'If delivery or public verification fails, stop this learned intervention and return to the native process within the same remaining budget. '
'Refuse when the state is unknown, already publicly passing, outside these conditions, or budget is insufficient. '
'This experience does not certify root cause or correctness; no hidden or future answers are available.')

def lis(a):
    d=[]
    for i,v in enumerate(a):d.append(1+max([d[j] for j in range(i) if a[j]<v] or [0]))
    return max(d or [0])
def beauty(a):return max(min(lis(p),lis(p[::-1])) for p in set(itertools.permutations(a)))
def dishes(rows):
    return max(sum(i*abs(rows[i-1][(ks[i-1]-1)%len(rows[i-1])]-rows[i][ks[i]]) for i in range(1,len(rows))) for ks in itertools.product(*(range(len(a)) for a in rows)))
def heldback(tid):
    rng=random.Random(160222);cases=[]
    for i in range(18):
        if tid=='taco_0914':
            a=[rng.randint(1,5) for _ in range(1+i%7)];inp='1\n'+str(len(a))+'\n'+' '.join(map(str,a))+'\n';answer=beauty(a)
        else:
            rows=[[rng.randint(1,20) for _ in range(rng.randint(1,4))] for _ in range(2+i%3)]
            inp='1\n'+str(len(rows))+'\n'+'\n'.join(str(len(a))+' '+' '.join(map(str,a)) for a in rows)+'\n';answer=dishes(rows)
        cases.append(dict(input=inp,expected=str(answer),comparison='tokens',scorer='s1',origin='frozen legal engineering input; exhaustive statement oracle; not independent task'))
    return cases

def selection():
    chosen=[];audit=[]
    for t in read(S15/'tasks.json'):
        if t['task_id'] in ('taco_0313','taco_0511'):continue
        p=S15/'branches'/t['task_id']/'G/response_1.json'
        if not p.exists():continue
        raw=read(p);c=raw['choices'][0];obs=delivery(c['message']['content'],c['finish_reason']);ok=not obs['code'] and c['finish_reason']=='length'
        audit.append(dict(task_id=t['task_id'],index=t['index'],eligible=ok))
        if not ok:continue
        wf=read(p.parent/'workflow.json');assert wf['events'][0]['stage']=='l1' and wf['events'][0]['budget']['calls']==1
        retry=wf['events'][1];assert retry['stage']=='l2a' and retry['request']['timeout_seconds']>20
        task={k:t[k] for k in ('task_id','dataset','difficulty','task_public','public_cases','reference_path','reference_sha256')};assert sha(task['reference_path'])==task['reference_sha256']
        ev=dict(task_public=t['task_public'],candidate_code='',public_feedback=dict(status='NO_COMPLETE_CODE',summary='No Python program was delivered; unfinished prose is not an algorithm to preserve.',public_cases=[],visibility='public'),generation_metadata=dict(finish_reason='length'),hook='before_native_retry',stage='l2a')
        chosen.append(dict(task=task,public_evidence=ev,lineage=dict(raw_path=str(p.relative_to(ROOT)),raw_sha256=sha(p),source='S15 G l1',prior_development_exposure=True,independent_holdout=False,remaining_calls=4,remaining_tokens=204800-raw['usage']['total_tokens'],observed_retry_seconds=retry['request']['timeout_seconds']),held_back=heldback(t['task_id'])))
        if len(chosen)==2:break
    assert [x['task']['task_id'] for x in chosen]==['taco_0914','taco_0657']
    return chosen,audit

def make_grant(reg,card,folder,task_ids):
    state=reg.state(card)
    files=[C/'summary.json',C/'F_held_back_review.json',C/'final_integrity.json']
    g=dict(artifact_sha256=card.artifact_sha256,previous_authorization_sha256=fingerprint(state['authorization']),prior_opportunities_used=state['opportunities_used'],additional_opportunities=len(task_ids),task_ids=task_ids,experiment_id=folder.name,stream_id=folder.name+'-F',effective_from=1,user_authorization='User requests S16-C2, explicitly additional bounded probation on 2-4 tasks; this plan grants exactly 2, no promotion.',review_evidence=[dict(path=str(p),sha256=sha(p)) for p in files])
    write(folder/'probation_grant.json',g);return folder/'probation_grant.json'

def main():
    selected,audit=selection();assert len(MEMORY.encode())<=1500
    card=WorkflowPolicy.from_dict(read(OLD/'summary.json')['cards'][0]['card']);assert sha(card.artifact_path)==card.artifact_sha256
    files=[Path(__file__),ROOT/'scripts/s16c2_probation.py',ROOT/'scripts/run_workflow_v2.py',ROOT/'scripts/experiment_s16b2_source.py',Path(card.artifact_path),OLD/'normalized_specification.json',e.prior.old.WORKER,e.prior.old.ACCEPTANCE]+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
    for item in selected:files += [ROOT/item['lineage']['raw_path'],Path(item['task']['reference_path'])]
    plan=dict(run_id=OUT.name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='real_experiment',frozen_files={str(p.relative_to(ROOT)):sha(p) for p in files},budgets={'solve':e.prior.config(12,400,1100000,65536)},per_task=dict(max_calls=2,max_tokens=147456,max_tools=40,wall_seconds=240),task_ids=[x['task']['task_id'] for x in selected],selection=fingerprint(selected),memory=MEMORY,memory_utf8_max=1500,knowledge_source_sha256=sha(OLD/'normalized_specification.json'),memory_provenance='Host-authored compact summary of same real specification, frozen before branches; no new target solution/algorithm. Not a new model-learned memory.',request_limits=dict(input_upper=65536,output=8192,temperature=0,thinking='disabled'),orders=[['G','M','F'],['M','F','G']],max_new_opportunities=2,hard_budget_usd=1.10,quoted_full_bound_usd=.3538944,price=dict(input_miss=.3,output=1.2,units='USD per million tokens',url='https://api-docs.deepseek.com/quick_start/pricing/',checked='2026-10-22'),new_generation_calls=0,controls=['S16-C G publicly passing actual program','S16-C M actual complete-syntax wrong-output program'],stopping='after each task final held-back review: suspend and stop further tasks if F applied but independent review fails; stop unknown sends/infrastructure failures; no replacement tasks/no automatic quota/no online stream',authorization='User requests S16-C2; 2 chronological tasks x G/M/F x <=2 solve calls; fresh $1.10 total cap; original v0 unchanged; two extra opportunities only.',history_learning=dict(tokens=10532,estimated_usd=.0058893),local_currency_cost=None)
    plan['protocol_hash']=fingerprint(plan)
    os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
    runner=e.ExperimentRunner(OUT,plan,sender_factory);(OUT/'tmp').mkdir();tempfile.tempdir=str(OUT/'tmp')
    write(OUT/'authorization.json',dict(run_id=OUT.name,protocol_hash=plan['protocol_hash'],allow_real_api=True,budgets=plan['budgets'],basis=plan['authorization']))
    write(OUT/'selection.json',dict(rule='first two S15 chronological G-l1 empty length failures, excluding source0313 and previous0511; no later outcomes used',audit=audit));write(OUT/'frozen_inputs.json',selected)
    # Preserve all historical files except live registry, which is append-only and separately snapshotted.
    historical={str(p):sha(p) for d in (OLD,C) for p in d.rglob('*') if p.is_file() and p.name not in ('registry.jsonl','registry.jsonl.lock')}
    write(OUT/'historical_before.json',historical)
    reg=RenewedRegistry(OLD/'registry.jsonl',e.FailureEvidenceStore(OLD/'evidence_F.jsonl'));(OUT/'registry_before.jsonl').write_bytes((OLD/'registry.jsonl').read_bytes())
    allresults={};error=None;status='STARTED';limits=Limits(input_token_upper=65536)
    try:
        for item in selected:
            task=item['task'];tid=task['task_id'];ref=Path(task['reference_path']).read_text()
            check=dict(public=runner.judge.run(tid,ref,task['public_cases']),held_back=runner.judge.run(tid,ref,item['held_back']),negative=runner.judge.run(tid,"print('INVALID')",task['public_cases']))
            write(OUT/'scorer_acceptance'/f'{tid}.json',check)
            assert check['public']['passed'] and check['held_back']['passed'] and not check['negative']['passed'],'scorer mismatch before API'
        controls=[]
        for arm in ('G','M'):
            wf=read(C/f'{arm}_workflow.json');code=wf['selected']['code'] if wf['selected'] else wf['last_candidate'];feedback=wf['events'][0]['public_feedback']
            ev=read(C/'checkpoint.json')['public_evidence'];payload=worker_context(ev['task_public'],code,feedback,dict(finish_reason='stop' if arm=='G' else 'length'),Budget(max_calls=2,max_tokens=147456,wall_seconds=240))
            d=validate_decision(runner.judge.decision(card,payload));controls.append(dict(source=str(C/f'{arm}_workflow.json'),input=payload,decision=d,passed=d['status']=='declined',engineering_context_projection=True))
        write(OUT/'controls.json',controls);assert all(c['passed'] for c in controls)
        grant=make_grant(reg,card,OUT,plan['task_ids']);reg.extend(card,grant,time.time());write(OUT/'registry_extended.json',reg.review(card))
        for index,item in enumerate(selected):
            task=item['task'];tid=task['task_id'];ev=item['public_evidence'];results={};allresults[tid]=results
            for arm in plan['orders'][index]:
                start=time.monotonic();before=runner.budgets['solve'].snapshot();local=Budget(**plan['per_task'])
                client=WorkflowClient(runner.transports['solve'],arm+'/'+tid,memory=MEMORY if arm=='M' else '',limits=limits);client.last=dict(text='```python\n\n```',code='',finish_reason='length')
                plugin=None;context=runner.context
                if arm=='F':
                    assert tid in plan['task_ids'] and sha(card.artifact_path)==card.artifact_sha256
                    context=card.evidence_fingerprint;plugin=e.WorkflowPlugin(reg,runner.stores['F'],context,stream_id=OUT.name+'-F',experiment_id=OUT.name,host_repair=client.host_repair,decision_runner=runner.judge.decision,synthetic=False)
                    plugin.begin(PublicTaskView.project(ev['task_public']),time.time());assert len(plugin.current['snapshot'].cards)==1
                    plugin.observe('', 'l1',PublicFeedback.project(ev['public_feedback']),dict(finish_reason='length'),time.time(),learnable=False)
                ctrl=PreparedController(client,lambda public,code:runner.judge.run(tid,code,task['public_cases']),context,plugin=plugin);ctrl.stages=(('l2a',0.),('l2b',0.))
                result=ctrl._solve(PublicTaskView.project(ev['task_public']),local,[],'',PublicFeedback.project(ev['public_feedback']),None,plugin)
                after=runner.budgets['solve'].snapshot();result.update(wall_seconds=time.monotonic()-start,tool_calls=after['tool_calls']-before['tool_calls'],tool_milliseconds=after['charged_or_reserved_tool_milliseconds']-before['charged_or_reserved_tool_milliseconds'])
                results[arm]=result;write(OUT/tid/f'{arm}_workflow.json',result);runner.save();print(tid,arm,result['status'],local.calls,local.used_tokens,flush=True)
                if any(x['status']=='UNKNOWN' for x in runner.transports['solve'].audit):raise RuntimeError('unknown request')
            for arm,res in results.items():
                code=res['selected']['code'] if res['selected'] else res['last_candidate'];(OUT/tid/f'{arm}_final.py').write_text(code)
                res['held_back']=runner.judge.run(tid,code,item['held_back']);write(OUT/tid/f'{arm}_held_back.json',res['held_back'])
            f=results['F'];applied=any(h['status']=='applied' for h in f.get('hook_events',[]))
            review=dict(registry=reg.review(card),operator_applied=applied,final_pass=f['held_back']['passed'],stop=applied and not f['held_back']['passed'])
            write(OUT/tid/'trial_review.json',review)
            if review['stop']:reg.suspend(card,'S16-C2 applied repair fails pre-frozen independent same-task oracle',time.time());status='STOPPED_SUSPENDED';break
            print('TASK_REVIEW',tid,{a:r['held_back']['tests_passed'] for a,r in results.items()},flush=True)
        else:status='BOUNDED_TRIALS_COMPLETED'
    except Exception as exc:error=dict(type=type(exc).__name__,message=str(exc));status='STOPPED_ERROR';print(status,error,flush=True)
    finally:
        runner.save();rows=[x for x in runner.transports['solve'].audit if x.get('raw_response')];stats={}
        for tid,results in allresults.items():
            stats[tid]={}
            for arm,res in results.items():
                usages=[r['raw_response']['usage'] for r in rows if r['request_id'].startswith(arm+'/'+tid+'/')]
                stats[tid][arm]=dict(public_pass=res['status']=='PUBLIC_ACCEPTED',held_back_pass=res.get('held_back',{}).get('passed'),calls=len(usages),input_tokens=sum(u['prompt_tokens'] for u in usages),output_tokens=sum(u['completion_tokens'] for u in usages),tokens=sum(u['total_tokens'] for u in usages),estimated_usd=sum((u['prompt_tokens']*.3+u['completion_tokens']*1.2)/1e6 for u in usages),tool_calls=res['tool_calls'],tool_milliseconds=res['tool_milliseconds'],wall_seconds=res['wall_seconds'],operator_applied=any(h['status']=='applied' for h in res.get('hook_events',[])),native_fallback_calls=len(res['events']) if arm=='F' else None,errors=[x for x in res['events'] if 'error' in x])
        write(OUT/'summary.json',dict(status=status,error=error,results=stats,registry=reg.review(card),budget=runner.budgets['solve'].snapshot(),actual_responses=len(rows),policy_unchanged=sha(card.artifact_path)==card.artifact_sha256,historical_changed=[p for p,h in historical.items() if sha(p)!=h],new_generation_calls=0));(OUT/'registry_after.jsonl').write_bytes((OLD/'registry.jsonl').read_bytes());print('SUMMARY',json.dumps(stats),flush=True)
    if error:raise RuntimeError('stopped; inspect saved state; do not auto-retry')
if __name__=='__main__':main()
