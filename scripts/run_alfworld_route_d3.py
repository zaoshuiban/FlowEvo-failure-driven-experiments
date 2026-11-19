"""D3 frozen whole-game diagnostic. No candidate learning or native bank update."""
import argparse
import io
import itertools
import json
import re
import shutil
import sys
import time
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'FlowEvo/src'))
import run_alfworld_route_d2 as D2
from failure_evo.runtime import BudgetExhausted
C, A = D2.C, D2.A
OUT = ROOT/'runs/alfworld_route_d3_online_20261119_01'
REPORT = ROOT/'reports'/OUT.name
D2ROOT = ROOT/'runs/alfworld_route_d2_independent_20261119_01'
SHA = '59ff438fafdb2675fc33d4a1543bce38088b59703cd9a85840cdd26407f67e04'
SEED = 'ROUTE_D3_ONLINE_V1'


class CapacityStop(Exception):
    pass


class DeliveryStop(Exception):
    pass


def public_history(initial, steps):
    # Empty action denotes the initial public observation; not an environment action.
    return [dict(action='', observation=initial['observation'])] + C.history(steps)


def full_user(goal, obs, commands, initial, steps, guidance):
    base = C._build_step_user(goal, obs, commands, [], [], guidance)
    history = ['\nRecent actions:', '  > [initial observation]', '    '+initial['observation']]
    for s in steps:
        history.extend(['  > '+s['action'], '    '+s['observation']])
    marker = '\nCurrent observation:\n'
    assert marker in base
    return base.replace(marker, '\n'.join(history)+'\n'+marker, 1)


def entry(goal, steps):
    # D2 destination receipt matching, plus required target-object check.
    obj = re.search(r'\btwo\s+([a-z]+)', goal.lower())
    dest = re.search(r'\b(?:in|on)\s+(?:a |the )?([a-z]+)\s*\.?$', goal.lower())
    if not obj or not dest:
        return None, 'PUBLIC_GOAL_UNRECOGNIZED'
    for i, s in enumerate(steps, 1):
        m = re.fullmatch(r'You move the (.+?) to the (.+?)\.', s['observation'])
        if (m and not s['done'] and not s['won'] and m[2].rsplit(' ',1)[0] == dest[1]
                and obj[1] in (m[1].rsplit(' ',1)[0], m[1].rsplit(' ',1)[0]+'s')):
            return i, 'FIRST_TARGET_PLACEMENT'
    return None, 'NO_NONTERMINAL_TARGET_PLACEMENT'


class Env(D2.Env):
    def step(self, action):
        s = self.study
        s.health()
        rows = s.env_events.records()
        n = sum(x['kind']=='STARTED' for x in rows)+1
        official = sum(x['kind']=='STARTED' and x['payload']['branch'].startswith('pairs/') for x in rows)
        if n > 2000 or (s.ident.startswith('pairs/') and official >= 1800):
            raise BudgetExhausted('ENVIRONMENT_LIMIT')
        p = dict(number=n, branch=s.ident, phase=self.phase, action=action)
        s.env_events.append('STARTED', p, time.time())
        try:
            r = self.base.step(action)
        except BaseException as e:
            s.env_events.append('ERROR', dict(p,error=type(e).__name__),time.time())
            raise
        s.env_events.append('RETURNED',dict(p,feedback=C.feedback(action,r)),time.time())
        return r


class Study(D2.Study):
    def __init__(self, root):
        self.root = root
        self.p = A.read(root/'protocol.json')
        self.ident = ''
        for path, h in self.p['files'].items():
            assert A.sha(Path(path)) == h, 'FROZEN_FILE_CHANGED: '+path
        self.budget = D2.PersistentBudget(root/'budget.jsonl',run_id=root.name,protocol_hash=A.digest(self.p),
            max_calls=2100,max_tokens=140000000,max_tools=650,max_cost_microusd=17000000,
            token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,
            max_tool_milliseconds=6500000,tool_milliseconds_upper=10000,wall_seconds=10800)
        self.events = D2.EvidenceStore(root/'events.jsonl')
        self.env_events = D2.EvidenceStore(root/'environment_actions.jsonl')
        es = self.env_events.records()
        assert {x['payload']['number'] for x in es if x['kind']=='STARTED'} == {x['payload']['number'] for x in es if x['kind']=='RETURNED'}, 'UNKNOWN_ENVIRONMENT'
        self.backend = D2.FrozenLinuxBackend(image=self.p['worker']['image'],worker_script=self.p['worker']['worker_script'])
        assert self.backend.manifest() == self.p['worker']

    def model(self, ident, messages, **unused):
        assert ident.startswith('pairs/') and '/action_' in ident, 'NO_LEARNING_OR_EXTRA_PLANNING'
        self.health()
        folder = self.root/'requests'/ident
        assert not (folder/'request.private.json').exists(), 'NO_REISSUE'
        wire = dict(model='deepseek-flash',messages=messages,max_tokens=1024,temperature=0,
                    thinking={'type':'disabled'},reasoning_effort='none',stream=False)
        size = len(C.canonical(wire).encode())
        A.commit(folder/'Input_Size.json',dict(bytes=size,limit_bytes=65536,input_token_upper=size+256))
        if size > 65536:
            raise CapacityStop('FULL_INPUT_CAPACITY_NO_TRUNCATION')
        self.budget.reserve_network(size+256,1024,job_id=ident,capability='model',request_id=ident,
            request_hash=A.digest(wire),policy=self.p['network_policy'],wire_hash=A.digest(wire))
        A.commit(folder/'request.private.json', wire)
        start = time.time()
        try:
            with D2.absolute_deadline(min(600,self.budget.remaining_seconds)):
                raw = D2.post_deepseek(wire,D2.configured_api_key(),budget=self.budget,request_id=ident,
                    policy=self.p['network_policy'],connection_factory=D2.capturing_factory(folder),
                    emit=lambda k,p:self.events.append(k,p,time.time()))
        finally:
            A.commit(folder/'Timing.json',dict(started=start,ended=time.time(),elapsed=time.time()-start))
        A.commit(folder/'response.json',raw)
        usage = D2.trusted_usage(raw)
        if not usage:
            self.budget.settle(ident)
            raise RuntimeError('UNKNOWN_USAGE')
        self.budget.settle(ident,tokens=usage['total_tokens'])
        if raw.get('model')!='deepseek-flash' or raw['choices'][0]['finish_reason']!='stop':
            raise DeliveryStop('MODEL_DELIVERY_FAILURE')
        return dict(text=raw['choices'][0]['message']['content'],usage=usage,request_id=ident,cache=False,wire_sha256=A.digest(wire))

    def reset(self, case):
        self.health()
        t = case['task']; game = Path(self.p['data_root'])/t['game']
        assert A.sha(game)==t['game_sha256'] and A.sha(game.with_name('traj_data.json'))==t['trajectory_sha256']
        base = D2.SelectedTrainEnv(self.p['data_root'],50)
        env = Env(base,self)
        try:
            with redirect_stdout(io.StringIO()):
                base.initialize(frozen_game_files=[str(game)])
                task,obs,cmds = base.reset()
            assert task.goal==case['goal'] and obs==case['initial']['observation'] and list(cmds)==case['initial']['commands'], 'INITIAL_STATE_MISMATCH'
            for step in case['steps']:
                assert step['action'] in cmds
                r = env.step(step['action'])
                assert C.feedback(step['action'],r)=={k:step[k] for k in C.feedback(step['action'],r)}, 'PREFIX_MISMATCH'
                obs,cmds=r.observation,list(r.admissible_commands)
            env.phase='suffix'
            return env,obs,cmds
        except BaseException:
            env.close(); raise

    def whole_game(self, case, index, arm):
        self.ident = f'pairs/{index:02d}/{arm}'
        folder = self.root/self.ident
        if (folder/'result.json').exists():
            return A.read(folder/'result.json')
        assert not (folder/'start.private.json').exists(), 'PARTIAL_BRANCH_NO_RESTART'
        started = time.time()
        env,obs,cmds = self.reset(case)
        start=dict(goal=case['goal'],observation=obs,commands=list(cmds),history=[],remaining_steps=50,
            game_sha256=case['task']['game_sha256'],skills_sha256=A.digest(case['skills']))
        A.commit(folder/'start.private.json',start)
        steps=[]; records=[]; state={}; used=False; active=False; anchor=None; first=None
        won=False; status='STEP_LIMIT'; reason='NO_NONTERMINAL_TARGET_PLACEMENT'; fallback=False
        skill_context,directives=C.guidance(case['skills'])
        try:
            while len(steps)<50:
                index_step=len(steps)+1; choice=None; response=None; decision=None
                if arm=='F' and not used:
                    anchor,reason=entry(case['goal'],steps)
                    if anchor is not None:
                        used=True; active=True; state={}
                        A.commit(folder/'Entry.json',dict(anchor=anchor,reason=reason,remaining=50-anchor,public_prefix_sha256=A.digest(steps)))
                phase='skill' if active else ('fallback' if used else 'pre_entry')
                if active:
                    try:
                        ctx=C.context_view(case['goal'],obs,cmds,public_history(case['initial'],steps),state)
                    except ValueError as e:
                        raise CapacityStop(str(e)) from e
                    decision=self.worker(self.root/'frozen/code.py',ctx,folder/'workers'/f'{index_step:02d}.json')
                    if first is None: first=decision['status']
                    state=decision.get('state',{})
                    if decision['status']=='applied': choice=decision['action']
                    else: active=False; fallback=True; phase='fallback'
                if choice is None:
                    if arm=='G':
                        user=C._build_step_user(case['goal'],obs,cmds,[s['action'] for s in steps],[s['observation'] for s in steps],skill_context)
                    else: user=full_user(case['goal'],obs,cmds,case['initial'],steps,skill_context)
                    response=self.model(self.ident+f'/action_{index_step:02d}',messages=[dict(role='system',content=C._build_system(directives)),dict(role='user',content=user)])
                    choice=C._parse_single_action(response['text'],cmds)
                s=C.feedback(choice,env.step(choice))
                record=dict(step=index_step,phase=phase,actor='MODEL' if response else 'SKILL',before_observation=obs,
                    legal_before=list(cmds),feedback=s,decision=decision,request=response,
                    parse=C.parsed_action(response['text'],cmds) if response else None)
                A.commit(folder/'steps'/f'{index_step:02d}.json',record)
                records.append(record);steps.append(s);obs=s['observation'];cmds=s['commands']
                if s['won']: won=True;status='SUCCESS';break
                if s['done']: status='ENVIRONMENT_DONE';break
                if len(steps)>=12 and [s['action'] for s in steps[-9:-6]]==[s['action'] for s in steps[-6:-3]]==[s['action'] for s in steps[-3:]]:
                    status='ACTION_CYCLE';break
                if len(records)>=3 and all('nothing happens' in s['observation'].lower() for s in steps[-3:]):
                    status='NO_PROGRESS';break
        except (CapacityStop,DeliveryStop) as e:
            status=type(e).__name__.upper()+':'+str(e)
        finally:
            env.close()
        workers=[A.read(p) for p in (folder/'workers').glob('*.json')]
        skill_actions=sum(r['actor']=='SKILL' for r in records)
        if not used: mode='NO_TRIGGER'
        elif not skill_actions and first=='declined':mode='ZERO_ACTION_DECLINE_NATIVE_'+('SUCCESS' if won else 'FAILURE')
        elif fallback:mode='SKILL_THEN_NATIVE_'+('SUCCESS' if won else 'FAILURE')
        elif won:mode='SKILL_DIRECT_COMPLETION'
        else:mode='SKILL_EPISODE_NOT_COMPLETED'
        value=dict(arm=arm,game_index=index,task_id=case['task']['task_id'],won=won,status=status,steps=steps,records=records,
            environment_actions=len(steps),logical_model_calls=sum(r['actor']=='MODEL' for r in records),worker_calls=len(workers),
            policy_actions=skill_actions,policy_errors=sum(w['result']['status']=='error' for w in workers),
            entry_anchor=anchor,entry_reason=reason,triggered=used,first_policy_status=first,fallback=fallback,completion_mode=mode,
            started=started,ended=time.time(),wall_seconds=time.time()-started,start_sha256=A.digest(start),cache_hits=0)
        A.commit(folder/'result.json',value)
        print(json.dumps({k:value[k] for k in ['game_index','arm','won','status','environment_actions','logical_model_calls','policy_actions','completion_mode']}),flush=True)
        return value


def prepare():
    OUT.mkdir(parents=True,exist_ok=True); REPORT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'protocol.json').exists(), 'ALREADY_FROZEN'
    d2p=A.read(D2ROOT/'protocol.json'); chain=A.read(D2ROOT/'Frozen_Candidate.json')
    assert A.sha(Path(chain['source']))==A.sha(D2ROOT/'frozen/code.py')==SHA
    (OUT/'frozen').mkdir(exist_ok=True)
    shutil.copyfile(D2ROOT/'frozen/code.py',OUT/'frozen/code.py')
    A.commit(OUT/'Candidate_Identity.json',dict(sha256=SHA,d2_chain=chain,new_game_content_read=False))
    inventory=A.read(D2ROOT/'exposure.private.json')
    rows=[r['task'] for r in inventory['eligible']+inventory['excluded']]
    exposure=A.protection(rows,[ROOT/'runs',Path.home()/'.local/share/flowevo'],OUT)
    assert not exposure['malformed']
    A.commit(OUT/'exposure.private.json',exposure)
    pool=[r['task'] for r in exposure['eligible'] if r['task']['split']=='train' and r['task']['task_type']=='pick_two_obj_and_place']
    chosen=[]; scene=Counter(); obj=Counter(); groups=set()
    while len(chosen)<12:
        available=[t for t in pool if t['group'] not in groups]
        if not available:break
        t=min(available,key=lambda t:(scene[t['scene']],obj[t['group'].split('-')[1]],A.digest([SEED,t['game_sha256']])))
        chosen.append(t);groups.add(t['group']);scene[t['scene']]+=1;obj[t['group'].split('-')[1]]+=1
    reserved_path=ROOT/'runs/alfworld_route_a_online_value_20261117_01/online/selection.private.json'
    reserved=[r['task'] for r in A.read(reserved_path)['tasks']]
    for key in ['group','game_sha256','trajectory_sha256','task_id']:
        assert not ({t[key] for t in chosen}&{t[key] for t in reserved})
    orders=list(itertools.permutations('GHF'))*2
    selection=dict(seed=SEED,tasks=chosen,orders=[list(x) for x in orders[:len(chosen)]],eligible_games=len(pool),eligible_groups=len({t['group'] for t in pool}),
        protected_games=len(exposure['protected_games']),reserved60_manifest_sha256=A.sha(reserved_path),reserved60_overlap=0,replacement_allowed=False,
        selection_algorithm='min(selected_scene_count, selected_object_category_count, SHA256(canonical([seed,game_sha256]))); distinct groups',
        seen_scene=[t['scene'] in exposure['protected_scenes'] for t in chosen])
    A.commit(OUT/'selection.private.json',selection)
    for arm in 'GHF':shutil.copyfile(D2ROOT/'bank.private.json',OUT/f'bank_{arm}.private.json')
    shutil.copyfile(D2ROOT/'bank.private.json',OUT/'bank.private.json')
    price=dict(checked='2026-11-19',source='https://api-docs.deepseek.com/quick_start/pricing/',flash_input_peak_uncached=0.30,flash_output_peak=1.20,pro_input_peak_uncached=1.32,pro_output_peak=3.96,units='USD per million tokens',provider_bill='unknown',documented_flash_version='DeepSeek-V4.1-Flash-1017')
    A.commit(OUT/'Price_Snapshot.json',price)
    files={p:h for p,h in d2p['files'].items() if not str(D2ROOT) in p}
    for p in [Path(__file__),Path(chain['source']),OUT/'frozen/code.py',OUT/'selection.private.json',OUT/'exposure.private.json',OUT/'Price_Snapshot.json',*[OUT/f'bank_{a}.private.json' for a in 'GHF'],OUT/'bank.private.json']:
        files[str(p)]=A.sha(p)
    files[d2p['worker']['worker_script']]=d2p['worker']['worker_sha256']
    protocol=dict(run_id=OUT.name,seed=SEED,files=files,worker=d2p['worker'],network_policy=d2p['network_policy'],data_root=d2p['data_root'],
        baseline='D2 frozen-success-library Flash controller, not full FlowEvo; same exemplar/insight retrieval, no success updates, no governance mutation or extra correction requests',
        full_history='initial public observation as empty-action record, then all actual action/observation receipts; no truncation. Same scope in H controller and F controller/Worker; unchanged context_view schema.',
        capacity='model wire <=65536 UTF8 bytes; Worker context <=65536; state <=4096; exceeds => failed trajectory, no truncation',
        trigger='first nonterminal public target-object placement to goal container; once only; empty initial state',
        fallback='H from actual state on decline/contract/runtime candidate error; original whole-episode 3x3 cycle/no-progress stopping preserved',
        model=dict(model='deepseek-flash',max_tokens=1024,temperature=0,thinking={'type':'disabled'},reasoning_effort='none',stream=False),
        limits=dict(games=12,trajectories=36,environment_per_game=50,model_calls=2100,official_environment=1800,all_environment=2000,workers=650,microusd=17000000,request_seconds=600,wall_seconds=10800),
        learning_calls=0,application_response_cache=False,bank_updates=False,price=price,
        ordinary_failures='capacity or delivered unusable response end trajectory; continue remaining fixed sample. Integrity/unknown/budget stop entire run; no resend.')
    A.commit(OUT/'protocol.json',protocol)
    A.commit(OUT/'Candidate_Freeze.json',dict(candidate_sha256=SHA,d2_chain=chain,worker=protocol['worker'],files=files,interfaces=protocol['full_history'],baseline=protocol['baseline']))
    shutil.copyfile(OUT/'Candidate_Freeze.json',REPORT/'Candidate_Freeze.json')
    print(json.dumps(selection,ensure_ascii=False,indent=2))


def fixtures(study):
    # Existing D2 cases only, one replay and one Worker each; no model calls.
    checks=[]
    for i in [0,1]:
        case=A.read(D2ROOT/f'checkpoints/{i:02d}_NORMAL.json')['checkpoint']
        assert entry(case['goal'],case['steps'])[0]==case['anchor']
        assert entry(case['goal'],case['steps'][:-1])[0] is None
        study.ident=f'fixtures/{i:02d}'
        env,obs,cmds=study.reset(case)
        try:
            ctx=C.context_view(case['goal'],obs,cmds,public_history(case['initial'],case['steps']),{})
            d=study.worker(OUT/'frozen/code.py',ctx,OUT/f'fixtures/{i:02d}/worker.json')
            expected='applied' if i==0 else 'declined'
            assert d['status']==expected
            if i==0:assert d['action']=='go to cabinet 2'
            else:assert d['reason']=='cannot parse goal'
            u=full_user(case['goal'],obs,cmds,case['initial'],case['steps'],'')
            assert all(s['observation'] in u for s in case['steps']) and case['initial']['observation'] in u
            checks.append(dict(fixture=i,entry=case['anchor'],decision=d['status'],history_complete=True))
        finally:env.close()
    # Regression checks use public archived feedback; no new-game data or execution.
    case=A.read(D2ROOT/'checkpoints/00_NORMAL.json')['checkpoint']
    wrong=dict(case['steps'][-1],observation='You move the soapbar 1 to the cabinet 1.')
    assert entry(case['goal'],[wrong])[0] is None
    assert entry(case['goal'],[dict(case['steps'][-1],done=True,won=True)])[0] is None
    A.commit(OUT/'Fixture_Acceptance.json',dict(passed=True,checks=checks,model_calls=0,environment_actions=13,worker_calls=2))


def run():
    study=Study(OUT)
    assert (REPORT/'Protocol.md').exists(), 'PROTOCOL_REQUIRED'
    if not (OUT/'Fixture_Acceptance.json').exists():fixtures(study)
    selected=A.read(OUT/'selection.private.json')
    results=[]
    for i,t in enumerate(selected['tasks']):
        case=D2.fresh(study,t,i)
        arms={}
        for arm in selected['orders'][i]:
            # Independent identical starting bank; no updater exists in D2 path.
            assert A.read(OUT/f'bank_{arm}.private.json')==A.read(OUT/'bank.private.json')
            arms[arm]=study.whole_game(case,i,arm)
        assert len({r['start_sha256'] for r in arms.values()})==1,'UNEQUAL_INITIAL_STATE'
        results.append(dict(game_index=i,task_id=t['task_id'],arms={a:{k:v[k] for k in ['won','status','environment_actions','logical_model_calls','policy_actions','completion_mode']} for a,v in arms.items()}))
        A.commit(OUT/f'pairs/{i:02d}/comparison.json',results[-1])
    A.commit(OUT/'Completed.json',dict(completed_at=C.stamp(),candidate_sha256=A.sha(OUT/'frozen/code.py'),results=results))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','run']);args=parser.parse_args()
    try:globals()[args.phase]()
    except BaseException as e:
        if args.phase=='run':A.commit(OUT/f'Stopped_{int(time.time())}.json',dict(error_type=type(e).__name__,message=str(e),at=C.stamp()))
        raise
