"""D5: frozen s1, full takeover versus exactly eight executed skill actions."""
import argparse,itertools,json,re,shutil,time
from collections import Counter
from pathlib import Path
import run_alfworld_route_d4 as D4
D,A,C=D4.D,D4.A,D4.C
ROOT=D4.ROOT
OLD=D4.OUT
OUT=ROOT/'runs/alfworld_route_d5_takeover_scope_20261119_01'
REPORT=ROOT/'reports'/OUT.name
SHA='c0d6ea0b3c9848cc52ed69a94c31554a271b73e09a5bcf574cf6c9f3c3b68079'
SEED='ROUTE_D5_TAKEOVER_SCOPE_V1'
WINDOW=8
signature=D4.signature


class Env(D4.Env):
    def step(self,action):
        s=self.study;s.health();rows=s.env_events.records();n=sum(x['kind']=='STARTED' for x in rows)+1
        fixture_count=sum(x['kind']=='STARTED' and '/fixtures/' in x['payload']['branch'] for x in rows)
        if n>5000 or ('/fixtures/' in s.ident and fixture_count>=100):raise D.BudgetExhausted('ENVIRONMENT_LIMIT')
        p=dict(number=n,branch=s.ident,phase=self.phase,action=action);s.env_events.append('STARTED',p,time.time())
        try:r=self.base.step(action)
        except BaseException as e:s.env_events.append('ERROR',dict(p,error=type(e).__name__),time.time());raise
        s.env_events.append('RETURNED',dict(p,feedback=C.feedback(action,r)),time.time());return r


# D4.reset delegates environment accounting to its module's Env. The common
# replay implementation remains unchanged; this process-local adapter only sets
# D5's resource caps and journal. Original D4 files and runs are never written.
D4.Env=Env


class Study(D4.Study):
    def __init__(self):
        self.root=OUT;self.p=A.read(OUT/'protocol.json');self.ident=''
        for path,h in self.p['files'].items():assert A.sha(Path(path))==h,'FROZEN_COMPONENT_CHANGED: '+path
        self.budget=D.D2.PersistentBudget(OUT/'budget.jsonl',run_id=OUT.name,protocol_hash=A.digest(self.p),max_calls=4000,max_tokens=270000000,max_tools=1600,
            max_cost_microusd=17000000,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=16000000,tool_milliseconds_upper=10000,wall_seconds=10800)
        self.events=D.D2.EvidenceStore(OUT/'events.jsonl');self.env_events=D.D2.EvidenceStore(OUT/'environment_actions.jsonl');es=self.env_events.records()
        assert {r['payload']['number'] for r in es if r['kind']=='STARTED'}=={r['payload']['number'] for r in es if r['kind']=='RETURNED'},'UNKNOWN_ENVIRONMENT_STATE'
        self.backend=D.D2.FrozenLinuxBackend(image=self.p['worker']['image'],worker_script=self.p['worker']['worker_script'])
        assert self.backend.manifest()==self.p['worker']
    def health(self):
        if self.budget.remaining_seconds<=0:raise RuntimeError('WALL_LIMIT')
        if self.budget.blocking_requests(self.p['network_policy']):raise RuntimeError('UNKNOWN_OR_PENDING_REQUEST')
    def generation(self,*args,**kwargs):raise RuntimeError('D5_ZERO_LEARNING_REQUESTS')


def branch(study,case,ident,code=None,stop_at_entry=False,reference_h=None,fixture_native_once=False,window=None):
    assert window in (None,8)
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
                    handback=dict(kind='CANDIDATE_DECLINED' if decision['status']=='declined' else 'CANDIDATE_ERROR',status=decision['status'],reason=decision['reason'],at_action=len(steps),remaining=50-len(steps),after_skill_actions=skill_actions,
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
            if len(steps)>=50:status='STEP_LIMIT';break
            if active and window is not None and skill_actions>=window:
                active=False
                handback=dict(kind='HOST_WINDOW_EXHAUSTED',status='host_window',reason='HOST_WINDOW_EXHAUSTED',at_action=len(steps),remaining=50-len(steps),after_skill_actions=skill_actions,
                    controller_signature_sha256=A.digest(signature(case,obs,cmds,steps)))
                A.commit(folder/'Handback.json',handback)
            if fixture_native_once and response:status='FIXTURE_NATIVE_CONTINUATION_OBSERVED';break
    except (D.CapacityStop,D.DeliveryStop) as e:status=type(e).__name__.upper()+':'+str(e)
    finally:env.close()
    workers=[A.read(p) for p in (folder/'workers').glob('*.json')]
    result=dict(ident=ident,won=won,status=status,window=window,stop_reason='ENVIRONMENT_WON' if won else ('TASK_BUDGET_EXHAUSTED' if len(steps)>=50 else status),anchor=len(prefix),remaining=50-len(steps),steps=steps,records=records,environment_actions=len(records),
        model_calls=sum(r['actor']=='MODEL' for r in records),worker_calls=len(workers),worker_ms=sum(w['milliseconds'] for w in workers),policy_actions=skill_actions,
        policy_errors=sum(w['result']['status']=='error' for w in workers),first_policy_status=first,handback=handback,shared_h=reference,
        start_sha256=A.digest(start),started=began,ended=time.time(),wall_seconds=time.time()-began)
    A.commit(folder/'result.json',result)
    print(json.dumps({k:result[k] for k in ['ident','won','status','environment_actions','model_calls','policy_actions','handback']}),flush=True)
    return result



def old_evidence():
    rows=[]
    for index,label in [(0,'Kettle'),(4,'Candle'),(6,'Ladle')]:
        for rep in [0,1]:
            stem=OLD/f'pairs/formal/{index:02d}/{rep}';cp=A.read(stem/'checkpoint.private.json');result=A.read(stem/'F3/result.json');n=cp['anchor']+1
            wp=stem/f'F3/workers/{n:02d}.json';worker=A.read(wp);target=re.search(r'\btwo ([a-z]+)',cp['goal'])[1]
            public=[dict(step=0,observation=cp['initial']['observation'],commands=cp['initial']['commands'])]+[dict(step=i,action=x['action'],observation=x['observation'],commands=x['commands']) for i,x in enumerate(cp['steps'],1)]
            mentions=[dict(step=x['step'],action=x.get('action'),observation=x['observation'],target_commands=[c for c in x['commands'] if re.search(r'\b'+target+r' \d+\b',c)]) for x in public if re.search(r'\b'+target+r' \d+\b',x['observation']) or any(re.search(r'\b'+target+r' \d+\b',c) for c in x['commands'])]
            instances=sorted(set(re.findall(r'\b'+target+r' \d+\b',C.canonical(public))))
            state=worker['raw']['value']['state'];unplaced=[dict(location=loc,instance=obj) for loc,objs in state['known_objects'].items() for obj in objs if obj.startswith(target+' ') and obj not in state['placed']]
            sources=[stem/'checkpoint.private.json',stem/'F3/result.json',wp,OLD/'frozen/selected.py']
            rows.append(dict(label=label,repetition=rep,goal=cp['goal'],entry_anchor=cp['anchor'],public_target_instances=instances,public_mentions=mentions,
                candidate_known_objects=state['known_objects'],candidate_placed=state['placed'],candidate_unplaced_targets=unplaced,
                second_target_location_status='UNKNOWN_IN_PUBLIC_ENTRY' if len(instances)==1 and not unplaced else 'REVIEW_REQUIRED',
                search_start=result['records'][0],source_path='process_observation -> choose_action known-object loop -> content-unknown location loop',
                source_hashes={str(p):A.sha(p) for p in sources}))
    A.commit(OUT/'Old_Public_Evidence.json',dict(rows=rows,interpretation='All six public prefixes reveal only the already-placed target instance. Unknown specific location does not prove each chosen search action necessary; later H success is not entry knowledge. No change to policy, window or sampling.'))
    shutil.copyfile(OUT/'Old_Public_Evidence.json',REPORT/'Old_Public_Evidence.json')


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);assert not (OUT/'protocol.json').exists()
    oldp=A.read(OLD/'protocol.json');selected=A.read(ROOT/'reports'/OLD.name/'Selected_Candidate.json');host=A.read(OLD/'Candidate_Host_Freeze.json')
    assert selected['selected_copy_sha256']==A.sha(OLD/'frozen/selected.py')==A.sha(Path(selected['selected']['source_path']))==SHA
    (OUT/'frozen').mkdir(exist_ok=True);shutil.copyfile(OLD/'frozen/selected.py',OUT/'frozen/code.py');shutil.copyfile(OLD/'bank.private.json',OUT/'bank.private.json')
    A.commit(OUT/'Candidate_Identity.json',dict(sha256=SHA,source_selected=selected,source_host_freeze_sha256=A.sha(OLD/'Candidate_Host_Freeze.json'),window=WINDOW,seed=SEED,source_and_window_fixed_before_sampling=True,sampling_rule='Recompute historical exposure exclusions; stratify unchanged public grammar.task goal by startswith put two; choose each layer 12 distinct groups by minimum prior-selected scene count, then object count, then SHA256 canonical [seed, game_sha256]. Put-two layer selected first; interleave layers in final list; no pilot filtering; six arm permutations each four times.'))
    old_evidence()
    inventory=A.read(OLD/'exposure.private.json');allrows=[x['task'] for x in inventory['eligible']+inventory['excluded']]
    exposure=A.protection(allrows,[ROOT/'runs',Path.home()/'.local/share/flowevo'],OUT);assert not exposure['malformed'];A.commit(OUT/'exposure.private.json',exposure)
    pool=[x['task'] for x in exposure['eligible'] if x['task']['split']=='train' and x['task']['task_type']=='pick_two_obj_and_place'];classified=[]
    for t in pool:
        raw=json.loads((Path(oldp['data_root'])/t['game']).read_text());grammar=raw['grammar'];obj,_=json.JSONDecoder().raw_decode(grammar[grammar.index('{'):]);assert len(obj['task'])==1
        goal=obj['task'][0]['rhs'].removeprefix('Your task is to: ');classified.append(dict(task=t,goal=goal,stratum='put_two' if goal.startswith('put two ') else 'other'))
    groups=set();scene=Counter();objects=Counter();layers={}
    for layer in ['put_two','other']:
        layers[layer]=[]
        for _ in range(12):
            choices=[x for x in classified if x['stratum']==layer and x['task']['group'] not in groups]
            if not choices:break
            row=min(choices,key=lambda r:(scene[r['task']['scene']],objects[r['task']['group'].split('-')[1]],A.digest([SEED,r['task']['game_sha256']])))
            layers[layer].append(row);t=row['task'];groups.add(t['group']);scene[t['scene']]+=1;objects[t['group'].split('-')[1]]+=1
    chosen=[rows[i] for i in range(12) for rows in [layers['put_two'],layers['other']] if i<len(rows)]
    reserved_path=ROOT/'runs/alfworld_route_a_online_value_20261117_01/online/selection.private.json';reserved=[x['task'] for x in A.read(reserved_path)['tasks']]
    for key in ['task_id','game_sha256','trajectory_sha256','group']:assert not ({r['task'][key] for r in chosen}&{r[key] for r in reserved})
    selection=dict(seed=SEED,tasks=[x['task'] for x in chosen],rows=chosen,eligible_games=len(pool),eligible_groups=len({t['group'] for t in pool}),pool_strata=dict(Counter(x['stratum'] for x in classified)),
        protected_games=len(exposure['protected_games']),orders=[list(x) for x in (list(itertools.permutations(['H','F_full','F8']))*4)[:len(chosen)]],repetitions=1,reserved60_sha256=A.sha(reserved_path),replacement=False,
        scene_seen=[x['task']['scene'] in exposure['protected_scenes'] for x in chosen])
    A.commit(OUT/'selection.private.json',selection)
    fixtures={name:A.read(OLD/f'pairs/formal/{i:02d}/0/checkpoint.private.json') for name,i in [('short',1),('window',4)]};A.commit(OUT/'fixtures.private.json',fixtures)
    files=dict(oldp['files'])
    for p in [Path(__file__),Path(D4.__file__),OUT/'frozen/code.py',OUT/'bank.private.json',OUT/'Candidate_Identity.json',OUT/'Old_Public_Evidence.json',OUT/'selection.private.json',OUT/'exposure.private.json',OUT/'fixtures.private.json']:
        files[str(p)]=A.sha(p)
    protocol=dict(run_id=OUT.name,files=files,worker=oldp['worker'],network_policy=oldp['network_policy'],data_root=oldp['data_root'],candidate_sha256=SHA,window=8,learning_calls=0,
        baseline='D4 full-history frozen-success-library Flash controller, no native library updates; not full FlowEvo',
        limits=dict(games=24,blocks=24,logical_results=72,model_calls=4000,environment=5000,fixture_environment=100,workers=1600,usd=17,wall_seconds=10800,request_seconds=600),
        intervention='After 8 actually executed skill actions, first honor won/done/global cycle/no-progress/budget; otherwise hand back H without a ninth Worker call. No reentry; no window hint or modified input.',
        block_admission='before next block require 200 request slots, 200 environment actions, 58 Worker slots, at least USD0.08018 worst-single-request reservation and positive time; every request still individually reserved, any midblock stop remains explicitly incomplete',
        sharing='D4 exact-signature zero-action declined H reference only; after window mutation always real H continuation',
        capacity='unchanged D3/D4 model wire and Worker context65536 bytes; state4096; no truncation',price=oldp['price'])
    A.commit(OUT/'protocol.json',protocol);A.commit(OUT/'Candidate_Host_Freeze.json',dict(candidate=selected,sha256=SHA,window=8,files=files,worker=oldp['worker']))
    shutil.copyfile(OUT/'Candidate_Host_Freeze.json',REPORT/'Candidate_Host_Freeze.json');A.commit(REPORT/'Sample_Manifest.json',dict(selection,execution_status='FROZEN_PENDING'))
    print(json.dumps(dict(eligible=len(pool),pool_strata=selection['pool_strata'],selected=len(chosen),layers={k:len(v) for k,v in layers.items()},candidate=SHA,window=8),ensure_ascii=False),flush=True)


def fixtures():
    study=Study();cases=A.read(OUT/'fixtures.private.json');results={}
    for name,case in cases.items():
        r=branch(study,case,'pairs/fixtures/'+name,OUT/'frozen/code.py',window=8);results[name]=r
    short=results['short'];long=results['window']
    assert short['won'] and short['policy_actions']<=8 and short['handback'] is None
    assert long['handback']['kind']=='HOST_WINDOW_EXHAUSTED' and long['policy_actions']==8 and long['worker_calls']==8 and long['model_calls']>=1
    assert long['handback']['at_action']==cases['window']['anchor']+8
    native=next(x for x in long['records'] if x['actor']=='MODEL');assert native['step']==cases['window']['anchor']+9
    assert sum(x['anchor']+x['environment_actions'] for x in results.values())<=100
    A.commit(OUT/'Fixture_Acceptance.json',dict(passed=True,short={k:short[k] for k in ['won','policy_actions','worker_calls','stop_reason']},window={k:long[k] for k in ['won','policy_actions','worker_calls','model_calls','handback','stop_reason']},no_window_reselection=True))


def admission(study,index):
    study.health();snapshot=study.budget.snapshot();environment_used=sum(x['kind']=='STARTED' for x in study.env_events.records())
    ok=snapshot['remaining_calls']>=200 and snapshot['remaining_tools']>=58 and snapshot['remaining_cost_microusd']>=80180 and 5000-environment_used>=200
    A.commit(OUT/f'admission/{index:02d}.json',dict(passed=ok,budget=snapshot,remaining_environment=5000-environment_used,remaining_seconds=study.budget.remaining_seconds))
    return ok


def formal():
    study=Study();assert A.read(OUT/'Fixture_Acceptance.json')['passed'];selection=A.read(OUT/'selection.private.json');done=[]
    for i,t in enumerate(selection['tasks']):
        if not admission(study,i):
            A.commit(OUT/'Admission_Stop.json',dict(next_index=i,completed_blocks=len(done),no_partial_new_block=True));return
        case=D.D2.fresh(study,t,i);assert case['goal']==selection['rows'][i]['goal']
        stem=f'pairs/formal/{i:02d}/0';pref=branch(study,case,stem+'/prefix',stop_at_entry=True)
        if pref['status']!='ENTRY_REACHED':
            row=dict(game_index=i,repetition=0,stratum=selection['rows'][i]['stratum'],prefix=stem+'/prefix',entry=False,shared_terminal=True,arms={a:dict(reference=stem+'/prefix',won=pref['won']) for a in ['H','F_full','F8']})
        else:
            cp=dict(case,steps=pref['steps'],anchor=len(pref['steps']));A.commit(OUT/stem/'checkpoint.private.json',cp);arms={}
            for arm in selection['orders'][i]:
                arms[arm]=branch(study,cp,stem+'/'+arm,OUT/'frozen/code.py' if arm!='H' else None,reference_h=stem+'/H' if arm!='H' else None,window=8 if arm=='F8' else None)
            assert len({r['start_sha256'] for r in arms.values()})==1,'BRANCH_START_MISMATCH'
            full=arms['F_full'];limited=arms['F8'];f=[x for x in full['records'] if x['actor']=='SKILL'];w=[x for x in limited['records'] if x['actor']=='SKILL']
            assert len(w)<=8 and len(f)>=len(w),'UNEXPLAINED_EARLY_DIVERGENCE'
            for x,y in zip(f,w):
                assert x['feedback']==y['feedback'] and x['decision']==y['decision'],'CANDIDATE_PREFIX_DIVERGENCE'
                a=A.read(OUT/stem/f'F_full/workers/{x["step"]:02d}.json');b=A.read(OUT/stem/f'F8/workers/{y["step"]:02d}.json');assert a['context_sha256']==b['context_sha256']
            A.commit(OUT/stem/'Window_Prefix_Validation.json',dict(passed=True,identical_executed_skill_actions=len(w),same_input_and_state=True,window_not_in_context=True))
            for arm in ['F_full','F8']:
                if arms[arm]['shared_h']:
                    assert arms[arm]['shared_h']['start_sha256']==arms['H']['start_sha256']
                    A.commit(OUT/stem/arm/'Resolved_Reference.json',dict(shared_trajectory=stem+'/H',sha256=A.sha(OUT/stem/'H/result.json'),won=arms['H']['won'],status=arms['H']['status'],no_duplicate_model_requests=True))
            row=dict(game_index=i,repetition=0,stratum=selection['rows'][i]['stratum'],prefix=stem+'/prefix',entry=True,shared_terminal=False,arms={a:dict(path=stem+'/'+a,reference=r['shared_h'],won=arms['H']['won'] if r['shared_h'] else r['won']) for a,r in arms.items()})
        A.commit(OUT/stem/'comparison.json',row);done.append(row)
    A.commit(OUT/'Completed.json',dict(completed_at=C.stamp(),candidate_sha256=SHA,window=8,blocks=done))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','fixtures','formal']);args=p.parse_args()
    try:globals()[args.phase]()
    except BaseException as e:
        if args.phase!='prepare':A.commit(OUT/f'Stopped_{args.phase}_{int(time.time())}.json',dict(error_type=type(e).__name__,message=str(e),at=C.stamp(),incomplete_block_must_not_be_scored_as_paired=True))
        raise
