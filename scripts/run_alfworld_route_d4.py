"""Bounded real-feedback revision, then shared-prefix H/F2/F3 evaluation."""
import argparse, ast, io, itertools, json, math, re, shutil, sys, time
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'FlowEvo/src'),'/private/tmp/flowevo_route_d1_tokenizers']
import run_alfworld_route_d3 as D
import run_alfworld_route_d1 as D1
import run_alfworld_revision_feedback as R
A,C=D.A,D.C
OUT=ROOT/'runs/alfworld_route_d4_feedback_revision_20261119_01'
REPORT=ROOT/'reports'/OUT.name
OLD=D.OUT
SEED='ROUTE_D4_FEEDBACK_REVISION_V1'
DEV=[0,11,10]
SYSTEM=C.SOURCE_CONTRACT+'''
Revise the supplied complete program using real refusal and execution feedback.
Return one JSON object with complete code, description and applicability. Keep
descriptions brief. Deliver Python in FINAL content, not reasoning. No classes,
nonlocal, global, filesystem, network, dynamic execution, reflection or model calls.
The input is exactly goal, observation, admissible_commands, history, state.
History starts with the initial public observation (empty action), followed by
every actual public action/observation receipt. Initial state is empty; returned
state is carried forward. Context <=65536 bytes, state <=4096, return <=8192.
Worker timeout 2 seconds, 256 MiB, one CPU, no network. Return applied with one
currently legal action, or declined to hand control back to the full-history
native controller. There is no success declaration: only environment won counts.
Based on real evidence revise goal understanding, necessary state maintenance,
and voluntary handback when behavior is confirmed to gain no new information or
task progress. Necessary return navigation after pickup or for second objects
must not be confused with stagnation. Do not decline everything to avoid failure.
Do not create exceptions keyed to game ID, scene, specific object names, fixed
instance IDs or fixed routes. Infer concrete parsing, search, state and handback
logic yourself. The host supplies no repaired regex or recovery implementation.
All skill and fallback actions share the original 50-action episode. Handback
does not clear prior steps or cycle/no-progress counters. Existing whole-episode
stopping rules remain: three identical consecutive 3-action blocks at >=12 steps,
or three consecutive Nothing happens observations. Learn to hand back BEFORE
stopping if no useful skill progress remains. The CD development criterion is
success or voluntary handback with at least 10 actions left for native continuation.
SoapBar and TissueBox development must be completed by the program itself after
the entry; native fallback does not pass those two criteria. Each submitted
candidate gets one real replay of each of those three old games, no more.
Any second submission receives full latest source and true feedback, not host
strategy edits. At most two submissions; first passing candidate is frozen.
'''


class Env(D.Env):
    def step(self,action):
        s=self.study;s.health();n=sum(x['kind']=='STARTED' for x in s.env_events.records())+1
        if n>5200:raise D.BudgetExhausted('ENVIRONMENT_LIMIT')
        p=dict(number=n,branch=s.ident,phase=self.phase,action=action)
        s.env_events.append('STARTED',p,time.time())
        try:r=self.base.step(action)
        except BaseException as e:s.env_events.append('ERROR',dict(p,error=type(e).__name__),time.time());raise
        s.env_events.append('RETURNED',dict(p,feedback=C.feedback(action,r)),time.time());return r


class Study(D.Study):
    def __init__(self):
        self.root=OUT;self.p=A.read(OUT/'protocol.json');self.ident=''
        for p,h in self.p['files'].items():assert A.sha(Path(p))==h,'FROZEN_COMPONENT_CHANGED: '+p
        common=dict(max_tool_milliseconds=30000000,tool_milliseconds_upper=10000,tool_cost_upper_microusd=0,wall_seconds=10800)
        self.budget=D.D2.PersistentBudget(OUT/'budget.jsonl',run_id=OUT.name+'/native',protocol_hash=A.digest(self.p),max_calls=3998,max_tokens=270000000,max_tools=3000,max_cost_microusd=16000000,token_rate_microusd_per_million=1200000,**common)
        self.generation_budget=D.D2.PersistentBudget(OUT/'generation_budget.jsonl',run_id=OUT.name+'/generation',protocol_hash=A.digest(self.p),max_calls=2,max_tokens=196608,max_tools=0,max_cost_microusd=1000000,token_rate_microusd_per_million=3960000,**common)
        self.events=D.D2.EvidenceStore(OUT/'events.jsonl');self.env_events=D.D2.EvidenceStore(OUT/'environment_actions.jsonl')
        es=self.env_events.records()
        assert {e['payload']['number'] for e in es if e['kind']=='STARTED'}=={e['payload']['number'] for e in es if e['kind']=='RETURNED'},'UNKNOWN_ENVIRONMENT'
        self.backend=D.D2.FrozenLinuxBackend(image=self.p['worker']['image'],worker_script=self.p['worker']['worker_script'])
        assert self.backend.manifest()==self.p['worker']
    def health(self):
        if min(self.budget.remaining_seconds,self.generation_budget.remaining_seconds)<=0:raise RuntimeError('WALL_LIMIT')
        for b in [self.budget,self.generation_budget]:
            if b.blocking_requests(self.p['network_policy']):raise RuntimeError('UNKNOWN_OR_PENDING_REQUEST')
    def reset(self,case):
        self.health();t=case['task'];game=Path(self.p['data_root'])/t['game']
        assert A.sha(game)==t['game_sha256'] and A.sha(game.with_name('traj_data.json'))==t['trajectory_sha256']
        base=D.D2.SelectedTrainEnv(self.p['data_root'],50);env=Env(base,self)
        try:
            with redirect_stdout(io.StringIO()):base.initialize(frozen_game_files=[str(game)]);task,obs,cmds=base.reset()
            assert task.goal==case['goal'] and obs==case['initial']['observation'] and list(cmds)==case['initial']['commands'],'INITIAL_MISMATCH'
            for s in case['steps']:
                assert s['action'] in cmds
                r=env.step(s['action']);actual=C.feedback(s['action'],r)
                assert actual=={k:s[k] for k in actual},'PREFIX_MISMATCH'
                obs,cmds=r.observation,list(r.admissible_commands)
            env.phase='suffix';return env,obs,cmds
        except BaseException:env.close();raise
    def generation(self,version,wire):
        self.health();folder=OUT/'requests'/'generation'/version
        assert not folder.exists(),'NO_GENERATION_REISSUE'
        measurement=D1.meter(wire);A.commit(folder/'input_measurement.json',measurement)
        assert measurement['estimated_input_upper']<=65536,'INPUT_CAPACITY_NO_TRUNCATION'
        b=self.generation_budget;rid='generation/'+version
        b.reserve_network(65536,32768,job_id=rid,capability='model',request_id=rid,request_hash=A.digest(wire),policy=self.p['network_policy'],wire_hash=A.digest(wire))
        A.commit(folder/'request.private.json',wire);started=time.time()
        try:
            with D.D2.absolute_deadline(min(600,b.remaining_seconds,self.budget.remaining_seconds)):
                raw=D.D2.post_deepseek(wire,D.D2.configured_api_key(),budget=b,request_id=rid,policy=self.p['network_policy'],connection_factory=D.D2.capturing_factory(folder),emit=lambda k,p:self.events.append(k,p,time.time()))
        finally:A.commit(folder/'Timing.json',dict(started=started,ended=time.time(),elapsed=time.time()-started))
        A.commit(folder/'response.json',raw);u=D.D2.trusted_usage(raw)
        if not u:b.settle(rid);raise RuntimeError('UNKNOWN_USAGE')
        b.settle(rid,tokens=u['total_tokens'])
        assert raw['model']=='deepseek-v4-pro' and u['input_tokens']<=measurement['estimated_input_upper']
        return raw


def signature(case,obs,cmds,steps):
    return dict(goal=case['goal'],observation=obs,commands=list(cmds),history=D.public_history(case['initial'],steps),remaining_steps=50-len(steps),
        game_sha256=case['task']['game_sha256'],skills_sha256=A.digest(case['skills']),controller_state='stateless full-history D3 controller',stopping_counters=C.history(steps))


def branch(study,case,ident,code=None,stop_at_entry=False,reference_h=None,fixture_native_once=False):
    study.ident=ident;folder=OUT/ident
    if (folder/'result.json').exists():return A.read(folder/'result.json')
    assert not (folder/'start.private.json').exists(),'PARTIAL_BRANCH_NO_RESTART'
    began=time.time();env,obs,cmds=study.reset(case)
    prefix=list(case['steps']);steps=list(prefix);records=[];state={};active=code is not None
    start=signature(case,obs,cmds,steps);A.commit(folder/'start.private.json',start)
    won=False;status='STEP_LIMIT';handback=None;first=None;reference=None;skill_actions=0
    guidance,directives=C.guidance(case['skills'])
    try:
        while len(steps)<50:
            if stop_at_entry and D.entry(case['goal'],steps)[0] is not None:status='ENTRY_REACHED';break
            n=len(steps)+1;choice=None;decision=None;response=None
            phase='skill' if active else ('fallback' if code else 'native')
            if active:
                try:ctx=C.context_view(case['goal'],obs,cmds,D.public_history(case['initial'],steps),state)
                except ValueError as e:raise D.CapacityStop(str(e)) from e
                decision=study.worker(code,ctx,folder/'workers'/f'{n:02d}.json')
                if first is None:first=decision['status']
                state=decision.get('state',{})
                if decision['status']=='applied':choice=decision['action'];skill_actions+=1
                else:
                    active=False;phase='fallback'
                    handback=dict(status=decision['status'],reason=decision['reason'],at_action=len(steps),remaining=50-len(steps),after_skill_actions=skill_actions,
                        controller_signature_sha256=A.digest(signature(case,obs,cmds,steps)))
                    A.commit(folder/'Handback.json',handback)
                    if not skill_actions and decision['status']=='declined' and reference_h:
                        assert handback['controller_signature_sha256']==A.digest(start),'ZERO_ACTION_STATE_CHANGED'
                        reference=dict(trajectory=reference_h,start_sha256=A.digest(start),rule='zero actions + declined + identical H input/bank/budget/controller/stopping history; outcome-blind')
                        status='SHARED_H_REFERENCE';break
            if choice is None:
                user=D.full_user(case['goal'],obs,cmds,case['initial'],steps,guidance)
                response=study.model(ident+f'/action_{n:02d}',messages=[dict(role='system',content=C._build_system(directives)),dict(role='user',content=user)])
                choice=C._parse_single_action(response['text'],cmds)
            fb=C.feedback(choice,env.step(choice))
            rec=dict(step=n,actor='MODEL' if response else 'SKILL',phase=phase,before_observation=obs,legal_before=list(cmds),feedback=fb,decision=decision,request=response,parse=C.parsed_action(response['text'],cmds) if response else None)
            A.commit(folder/'steps'/f'{n:02d}.json',rec);records.append(rec);steps.append(fb);obs=fb['observation'];cmds=fb['commands']
            if fb['won']:won=True;status='SUCCESS';break
            if fb['done']:status='ENVIRONMENT_DONE';break
            if len(steps)>=12 and [s['action'] for s in steps[-9:-6]]==[s['action'] for s in steps[-6:-3]]==[s['action'] for s in steps[-3:]]:status='ACTION_CYCLE';break
            if len(steps)>=3 and all('nothing happens' in s['observation'].lower() for s in steps[-3:]):status='NO_PROGRESS';break
            if fixture_native_once and response:status='FIXTURE_NATIVE_CONTINUATION_OBSERVED';break
    except (D.CapacityStop,D.DeliveryStop) as e:status=type(e).__name__.upper()+':'+str(e)
    finally:env.close()
    workers=[A.read(p) for p in (folder/'workers').glob('*.json')]
    result=dict(ident=ident,won=won,status=status,anchor=len(prefix),remaining=50-len(steps),steps=steps,records=records,environment_actions=len(records),
        model_calls=sum(r['actor']=='MODEL' for r in records),worker_calls=len(workers),worker_ms=sum(w['milliseconds'] for w in workers),policy_actions=skill_actions,
        policy_errors=sum(w['result']['status']=='error' for w in workers),first_policy_status=first,handback=handback,shared_h=reference,
        start_sha256=A.digest(start),started=began,ended=time.time(),wall_seconds=time.time()-began)
    A.commit(folder/'result.json',result)
    print(json.dumps({k:result[k] for k in ['ident','won','status','environment_actions','model_calls','policy_actions','handback']}),flush=True)
    return result


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'protocol.json').exists()
    oldp=A.read(OLD/'protocol.json');freeze=A.read(OLD/'Candidate_Freeze.json')
    assert A.sha(OLD/'frozen/code.py')==freeze['candidate_sha256']==D.SHA
    (OUT/'frozen').mkdir(exist_ok=True);shutil.copyfile(OLD/'frozen/code.py',OUT/'frozen/v2.py')
    shutil.copyfile(OLD/'bank.private.json',OUT/'bank.private.json')
    cases={};evidence=[];sources={}
    for i in [0,3,4,5,6,11,10]:
        cp=OLD/f'native/{i:02d}/case.private.json';rp=OLD/f'pairs/{i:02d}/F/result.json';ep=OLD/f'pairs/{i:02d}/F/Entry.json'
        case=A.read(cp);result=A.read(rp);anchor=A.read(ep)['anchor']
        cases[str(i)]=dict(case,steps=result['steps'][:anchor],anchor=anchor)
        selected_records=result['records'] if i in DEV else result['records'][:anchor]
        # All future receipts below are from this same already-exposed F branch.
        rows=[dict(step=r['step'],actor=r['actor'],action=r['feedback']['action'],observation=r['feedback']['observation'],admissible_commands_after=r['feedback']['commands'],won=r['feedback']['won'],done=r['feedback']['done'],decision=r['decision']) for r in selected_records]
        worker_path=OLD/f'pairs/{i:02d}/F/workers/{anchor+1:02d}.json'
        first=A.read(worker_path)
        evidence.append(dict(label=case['task']['group'].split('-')[1],goal=case['goal'],initial=case['initial'],entry_anchor=anchor,public_incremental_receipts=rows,entry_worker=first,
            terminal_result=dict(won=result['won'],status=result['status']) if i in DEV else None,
            native_suffix_is_real_recovery_demonstration=(i==0),sources=[str(cp),str(rp),str(ep),str(worker_path)]))
        for p in [cp,rp,ep,worker_path]:sources[str(p)]=A.sha(p)
    package=dict(source_version='D1_v2_used_in_D3',source_sha256=D.SHA,code=(OUT/'frozen/v2.py').read_text(),interface=C.SOURCE_CONTRACT,
        evidence=evidence,source_hashes=sources,scope='Only exposed D3 F-branch public receipts; no new evaluation goals, private state, oracle, other-arm future or host repairs.')
    A.commit(OUT/'Feedback_Package.json',package);A.commit(OUT/'development.private.json',cases)
    config={k:v for k,v in A.read(ROOT/'runs/alfworld_route_d1_pro_compilation_20261118_01/requests/v2/request.private.json').items() if k!='messages'}
    A.commit(OUT/'Generation_Config.json',config)
    # Freeze sampling algorithm before any candidate; no environment loads here.
    inv=A.read(OLD/'exposure.private.json');allrows=[x['task'] for x in inv['eligible']+inv['excluded']]
    exposure=A.protection(allrows,[ROOT/'runs',Path.home()/'.local/share/flowevo'],OUT);assert not exposure['malformed']
    A.commit(OUT/'exposure.private.json',exposure)
    pool=[r['task'] for r in exposure['eligible'] if r['task']['split']=='train' and r['task']['task_type']=='pick_two_obj_and_place']
    classified=[]
    for t in pool:
        # Read only public task RHS from eligible files; never evaluate walkthrough or PDDL.
        raw=json.loads((Path(oldp['data_root'])/t['game']).read_text())
        grammar=raw['grammar'];body=grammar[grammar.index('{'):]
        grammar_object,_=json.JSONDecoder().raw_decode(body)
        tasks=grammar_object['task'];assert len(tasks)==1
        goal=tasks[0]['rhs'].removeprefix('Your task is to: ')
        classified.append(dict(task=t,goal=goal,stratum='put_two' if goal.startswith('put two ') else 'other'))
    chosen=[];groups=set();scene=Counter();objects=Counter()
    for stratum in ['put_two','other']:
        for _ in range(6):
            candidates=[r for r in classified if r['stratum']==stratum and r['task']['group'] not in groups]
            if not candidates:break
            row=min(candidates,key=lambda r:(scene[r['task']['scene']],objects[r['task']['group'].split('-')[1]],A.digest([SEED,r['task']['game_sha256']])))
            chosen.append(row);t=row['task'];groups.add(t['group']);scene[t['scene']]+=1;objects[t['group'].split('-')[1]]+=1
    # Alternate strata in game order, independently of outcomes.
    chosen=sorted(chosen,key=lambda r:(sum(1 for x in chosen[:chosen.index(r)] if x['stratum']==r['stratum']),r['stratum']!='put_two'))
    reserved=ROOT/'runs/alfworld_route_a_online_value_20261117_01/online/selection.private.json'
    protected=[x['task'] for x in A.read(reserved)['tasks']]
    for k in ['group','task_id','game_sha256','trajectory_sha256']:assert not ({r['task'][k] for r in chosen}&{r[k] for r in protected})
    orders=list(itertools.permutations(['H','F2','F3']))*4
    selection=dict(seed=SEED,tasks=[r['task'] for r in chosen],rows=chosen,eligible_games=len(pool),eligible_groups=len({t['group'] for t in pool}),stratum_pool=dict(Counter(r['stratum'] for r in classified)),
        repetitions=2,orders=[list(x) for x in orders[:2*len(chosen)]],reserved60_sha256=A.sha(reserved),replacement=False)
    A.commit(OUT/'selection.private.json',selection)
    files=dict(oldp['files'])
    for p in [Path(__file__),Path(D.__file__),Path(D1.__file__),Path(R.__file__),OUT/'Feedback_Package.json',OUT/'development.private.json',OUT/'Generation_Config.json',OUT/'frozen/v2.py',OUT/'bank.private.json',OUT/'selection.private.json',OUT/'exposure.private.json',D1.TOKENIZER]:files[str(p)]=A.sha(p)
    protocol=dict(run_id=OUT.name,files=files,data_root=oldp['data_root'],network_policy=oldp['network_policy'],worker=oldp['worker'],system_prompt_sha256=A.digest(SYSTEM),generation_config=config,
        limits=dict(generation_calls=2,all_model_calls=4000,environment=5200,workers=3000,usd=17,wall_seconds=10800,request_seconds=600),
        budget_allocation='Pro generation <=2 and USD1; native <=3998 and USD16; combined <=4000/USD17, no borrowing. Uniform per-model peak output rate reservations.',
        development_indices=DEV,selection_seed=SEED,sharing='zero-action declined only; exact start signature incl public history, bank, budget, controller, all episode stopping history; H outcome-blind reference even when H ran later',
        main_comparisons=['F3 vs F2','F3 vs H'],host_contract_repair=False,bank_updates=False,history='exact D3 full_user and public_history/context_view; no truncation',
        source=D.SHA,price=oldp['price'],ordinary_stop='cycle/no-progress/50 total steps retained; candidate may voluntarily decline before cycle. H fallback keeps all counters.')
    A.commit(OUT/'protocol.json',protocol)
    A.commit(OUT/'Candidate_Host_Freeze.json',dict(old_candidate_sha256=D.SHA,files=files,worker=oldp['worker'],host_repair=False))
    for name in ['Candidate_Host_Freeze.json','Feedback_Package.json','Generation_Config.json']:shutil.copyfile(OUT/name,REPORT/name)
    preview=dict(config,messages=[dict(role='system',content=SYSTEM),dict(role='user',content=C.canonical(dict(material=package,previous_submission=None,development_feedback=None)))])
    A.commit(OUT/'First_Request_Preview.json',preview);A.commit(OUT/'Input_Preflight.json',D1.meter(preview))
    print(json.dumps(dict(eligible=len(pool),strata=selection['stratum_pool'],selected=[(r['stratum'],r['task']['task_id']) for r in chosen],input=D1.meter(preview)),ensure_ascii=False),flush=True)


def fixture():
    study=Study();case=A.read(OUT/'development.private.json')['10']
    original=A.read(OLD/'pairs/10/F/result.json');action=original['records'][case['anchor']]['feedback']['action']
    code="def environment_operator(context):\n if not context['state']:\n  return {'status':'applied','action':"+repr(action)+",'state':{'once':True},'reason':'contract fixture only'}\n return {'status':'declined','state':{},'reason':'contract fixture handback'}\n"
    path=OUT/'fixtures/contract_only.py';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(code)
    result=branch(study,case,'pairs/fixtures/handback',path,fixture_native_once=True)
    assert result['policy_actions']==1 and result['model_calls']==1 and result['handback']['at_action']==case['anchor']+1
    native=result['records'][-1];assert native['actor']=='MODEL' and native['step']==case['anchor']+2
    A.commit(OUT/'Contract_Acceptance.json',dict(passed=True,host_patch_needed=False,actual_mutation_action=action,handback=result['handback'],native_continued=True,steps_not_reset=True,fixture_not_in_learning_material=True))


def generate(version):
    study=Study();assert A.read(OUT/'Contract_Acceptance.json')['passed'];assert not (OUT/'Selected.json').exists()
    assert version in ['s1','s2']
    previous=None;feedback=None
    if version=='s2':
        feedback=A.read(OUT/'evaluations/s1/Acceptance.json');assert not feedback['passed']
        sub=A.read(OUT/'candidates/s1/submission.json')
        previous=dict(version='s1',code=Path(sub['code_path']).read_text() if sub['code_path'] else None,delivery=sub['extraction']['errors'],static=sub['static'],review=A.read(OUT/'candidates/s1/Review.json') if (OUT/'candidates/s1/Review.json').exists() else None)
        feedback=dict(feedback,actual_runs=[A.read(p) for p in sorted((OUT/'evaluations/s1').glob('*/result.json'))])
        # Strip no public observations, but avoid duplicated prefix in every record.
        feedback['actual_runs']=[dict(ident=x['ident'],won=x['won'],status=x['status'],handback=x['handback'],anchor=x['anchor'],records=[{k:r[k] for k in ['step','actor','decision','feedback','legal_before']} for r in x['records']]) for x in feedback['actual_runs']]
    payload=dict(material=A.read(OUT/'Feedback_Package.json'),previous_submission=previous,development_feedback=feedback)
    wire=dict(A.read(OUT/'Generation_Config.json'),messages=[dict(role='system',content=SYSTEM),dict(role='user',content=C.canonical(payload))])
    A.commit(OUT/'slots'/f'{version}.json',dict(version=version,created=C.stamp()))
    raw=study.generation(version,wire);sub=R.submitted(OUT,version,raw,dict(kind='real_reuse_feedback_revision'))
    if not sub['static']['passed']:A.commit(OUT/f'evaluations/{version}/Acceptance.json',dict(passed=False,reason='DELIVERY_OR_STATIC_FAILURE',version=version))
    print(json.dumps(dict(version=version,static=sub['static'],code_path=sub['code_path'],sha256=sub['code_sha256']),ensure_ascii=False),flush=True)


def evaluate(version):
    study=Study();sub=A.read(OUT/f'candidates/{version}/submission.json');review=A.read(OUT/f'candidates/{version}/Review.json')
    assert sub['static']['passed'] and review['passed'];code=Path(sub['code_path']);assert A.sha(code)==sub['code_sha256']
    cases=A.read(OUT/'development.private.json');checks=[]
    for i in DEV:
        result=branch(study,cases[str(i)],f'pairs/development/{version}/{i:02d}',code)
        A.commit(OUT/f'evaluations/{version}/{i:02d}/result.json',result)
        if i in [0,10]:passed=result['won'] and result['handback'] is None
        else:passed=(result['won'] and result['handback'] is None) or bool(result['handback'] and result['handback']['status']=='declined' and result['handback']['remaining']>=10)
        passed=passed and result['policy_errors']==0
        checks.append(dict(case=i,passed=passed,won=result['won'],policy_actions=result['policy_actions'],status=result['status'],handback=result['handback']))
    for i in [0,3,4,5,6]:
        case=cases[str(i)];last=case['steps'][-1]
        ctx=C.context_view(case['goal'],last['observation'],last['commands'],D.public_history(case['initial'],case['steps']),{})
        study.worker(code,ctx,OUT/f'evaluations/{version}/output_only/{i:02d}.json')
    acceptance=dict(version=version,passed=all(x['passed'] for x in checks),checks=checks,code_sha256=A.sha(code))
    A.commit(OUT/f'evaluations/{version}/Acceptance.json',acceptance)
    if acceptance['passed']:
        shutil.copyfile(code,OUT/'frozen/selected.py')
        A.commit(OUT/'Selected.json',dict(version=version,code_sha256=A.sha(code),selected_at=C.stamp(),reason='first submission passing all three fixed development cases',source_path=str(code)))
    print(json.dumps(acceptance,ensure_ascii=False),flush=True)


def formal():
    study=Study();selected=A.read(OUT/'Selected.json');assert A.sha(OUT/'frozen/selected.py')==selected['code_sha256']
    manifest=A.read(OUT/'selection.private.json');done=[]
    for i,t in enumerate(manifest['tasks']):
        case=D.D2.fresh(study,t,i);assert case['goal']==manifest['rows'][i]['goal'],'STRATIFICATION_GOAL_MISMATCH'
        for rep in range(2):
            stem=f'pairs/formal/{i:02d}/{rep}';pref=branch(study,case,stem+'/prefix',stop_at_entry=True)
            if pref['status']!='ENTRY_REACHED':
                row=dict(game_index=i,repetition=rep,stratum=manifest['rows'][i]['stratum'],prefix=stem+'/prefix',entry=False,shared_terminal=True,arms={a:dict(reference=stem+'/prefix',won=pref['won']) for a in ['H','F2','F3']})
            else:
                cp=dict(case,steps=pref['steps'],anchor=len(pref['steps']));A.commit(OUT/stem/'checkpoint.private.json',cp);arms={}
                for arm in manifest['orders'][i*2+rep]:
                    code=None if arm=='H' else OUT/('frozen/v2.py' if arm=='F2' else 'frozen/selected.py')
                    arms[arm]=branch(study,cp,stem+'/'+arm,code,reference_h=stem+'/H' if arm!='H' else None)
                assert len({r['start_sha256'] for r in arms.values()})==1,'BRANCH_START_MISMATCH'
                for arm in ['F2','F3']:
                    if arms[arm]['shared_h']:
                        assert arms[arm]['shared_h']['start_sha256']==arms['H']['start_sha256']
                        A.commit(OUT/stem/arm/'Resolved_Reference.json',dict(shared_trajectory=stem+'/H',sha256=A.sha(OUT/stem/'H/result.json'),won=arms['H']['won'],status=arms['H']['status'],no_duplicate_model_requests=True))
                row=dict(game_index=i,repetition=rep,stratum=manifest['rows'][i]['stratum'],prefix=stem+'/prefix',entry=True,shared_terminal=False,arms={a:dict(path=stem+'/'+a,reference=r['shared_h'],won=arms['H']['won'] if r['shared_h'] else r['won']) for a,r in arms.items()})
            A.commit(OUT/stem/'comparison.json',row);done.append(row)
    A.commit(OUT/'Completed.json',dict(completed_at=C.stamp(),selected=selected,blocks=done))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','fixture','generate','evaluate','formal']);p.add_argument('--version',choices=['s1','s2']);args=p.parse_args()
    try:globals()[args.phase](args.version) if args.phase in ['generate','evaluate'] else globals()[args.phase]()
    except BaseException as e:
        if args.phase!='prepare':A.commit(OUT/f'Stopped_{args.phase}_{int(time.time())}.json',dict(error_type=type(e).__name__,message=str(e),at=C.stamp()))
        raise
