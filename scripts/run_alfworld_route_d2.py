"""Frozen v2 independent reuse; new games, paired G/F, no learning channel."""
import argparse,io,json,re,sys,time
from pathlib import Path
from contextlib import redirect_stdout
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
import run_alfworld_route_c_bounded_learning as C
from alfworld_revision_environment import SelectedTrainEnv
from alfworld_absolute_deadline import absolute_deadline,capturing_factory
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.evidence import EvidenceStore
from failure_evo.network_transport import post_deepseek
from failure_evo.model_api import configured_api_key
from failure_evo.run_health import trusted_usage
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from alfworld_.skill_library import SkillLibrary
A=C.A

def repeated_retake(goal,steps):
    placed={};counts={};anchors=[]
    obj=re.search(r'\btwo\s+([a-z]+)',goal.lower());dest=re.search(r'\b(?:in|on)\s+(?:a |the )?([a-z]+)\s*\.?$',goal.lower())
    if not obj or not dest:return []
    for i,s in enumerate(steps,1):
        move=re.fullmatch(r'You move the (.+?) to the (.+?)\.',s['observation']);take=re.fullmatch(r'You pick up the (.+?) from the (.+?)\.',s['observation'])
        if move:placed[move[1]]=move[2]
        if take:
            if placed.get(take[1])==take[2] and take[2].rsplit(' ',1)[0]==dest[1] and obj[1] in (take[1].rsplit(' ',1)[0],take[1].rsplit(' ',1)[0]+'s'):
                key=(take[1],take[2]);counts[key]=counts.get(key,0)+1
                if counts[key]>=2:anchors.append(i)
            placed.pop(take[1],None)
    return anchors

class Env:
    def __init__(self,base,study):self.base=base;self.study=study;self.phase='prefix'
    def step(self,action):
        s=self.study;s.health();n=sum(x['kind']=='STARTED' for x in s.env_events.records())+1
        if n>1200:raise RuntimeError('ENVIRONMENT_LIMIT')
        p=dict(number=n,branch=s.ident,phase=self.phase,action=action);s.env_events.append('STARTED',p,time.time())
        try:r=self.base.step(action)
        except BaseException as e:s.env_events.append('ERROR',dict(p,error=type(e).__name__),time.time());raise
        s.env_events.append('RETURNED',dict(p,feedback=C.feedback(action,r)),time.time());return r
    def close(self):self.base.close()

class Study(C.Study):
    def __init__(self,root):
        self.root=root;self.p=A.read(root/'protocol.json');self.ident=''
        for path,h in self.p['files'].items():
            if A.sha(Path(path))!=h:raise RuntimeError('FROZEN_FILE_CHANGED')
        self.budget=PersistentBudget(root/'budget.jsonl',run_id=root.name,protocol_hash=A.digest(self.p),max_calls=800,max_tokens=13824000,max_tools=600,max_cost_microusd=17000000,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=6000000,tool_milliseconds_upper=10000,wall_seconds=10800)
        self.events=EvidenceStore(root/'events.jsonl');self.env_events=EvidenceStore(root/'environment_actions.jsonl');es=self.env_events.records()
        if {x['payload']['number'] for x in es if x['kind']=='STARTED'}!={x['payload']['number'] for x in es if x['kind']=='RETURNED'}:raise RuntimeError('UNKNOWN_ENVIRONMENT_STATE')
        self.backend=FrozenLinuxBackend(image=self.p['worker']['image'],worker_script=self.p['worker']['worker_script'])
        if self.backend.manifest()!=self.p['worker']:raise RuntimeError('WORKER_CHANGED')
    def health(self):
        if self.budget.remaining_seconds<=0:raise RuntimeError('WALL_LIMIT')
        if self.budget.blocking_requests(self.p['network_policy']):raise RuntimeError('UNKNOWN_OR_PENDING_REQUEST')
    def model(self,ident,messages,max_tokens=1024,json_output=False,cache=False):
        if not ident.startswith(('native/','pairs/')) or ident.endswith('/plan'):raise RuntimeError('ONLY_NATIVE_ACTION_CALLS')
        self.health();folder=self.root/'requests'/ident
        if (folder/'request.private.json').exists():raise RuntimeError('NO_AUTOMATIC_REQUEST_REISSUE')
        wire=dict(model='deepseek-flash',messages=messages,max_tokens=1024,temperature=0,thinking={'type':'disabled'},reasoning_effort='none',stream=False)
        size=len(C.canonical(wire).encode());A.commit(folder/'Input_Size.json',dict(bytes=size,limit_bytes=16000,input_token_upper=size+256))
        if size>16000:raise RuntimeError('INPUT_LIMIT_NO_TRUNCATION')
        A.commit(folder/'request.private.json',wire);self.budget.reserve_network(size+256,1024,job_id=ident,capability='model',request_id=ident,request_hash=A.digest(wire),policy=self.p['network_policy'],wire_hash=A.digest(wire))
        start=time.time()
        try:
            with absolute_deadline(min(600,self.budget.remaining_seconds)):
                raw=post_deepseek(wire,configured_api_key(),budget=self.budget,request_id=ident,policy=self.p['network_policy'],connection_factory=capturing_factory(folder),emit=lambda k,p:self.events.append(k,p,time.time()))
        finally:A.commit(folder/'Timing.json',dict(started=start,ended=time.time(),elapsed=time.time()-start))
        A.commit(folder/'response.json',raw);usage=trusted_usage(raw)
        if not usage:self.budget.settle(ident);raise RuntimeError('UNKNOWN_USAGE')
        self.budget.settle(ident,tokens=usage['total_tokens'])
        if raw.get('model')!='deepseek-flash' or raw['choices'][0]['finish_reason']!='stop':raise RuntimeError('MODEL_DELIVERY_FAILURE')
        print(json.dumps(dict(request=ident,tokens=usage['total_tokens'])),flush=True)
        return dict(text=raw['choices'][0]['message']['content'],usage=usage,request_id=ident,cache=False,wire_sha256=A.digest(wire))
    def reset(self,case):
        self.health();t=case['task'];game=Path(self.p['data_root'])/t['game']
        if A.sha(game)!=t['game_sha256'] or A.sha(game.with_name('traj_data.json'))!=t['trajectory_sha256']:raise RuntimeError('GAME_HASH_CHANGED')
        base=SelectedTrainEnv(self.p['data_root'],50);env=Env(base,self)
        try:
            with redirect_stdout(io.StringIO()):base.initialize(frozen_game_files=[str(game)]);task,obs,cmds=base.reset()
            assert task.goal==case['goal'] and obs==case['initial']['observation'] and list(cmds)==case['initial']['commands']
            for step in case['steps']:
                assert step['action'] in cmds
                r=env.step(step['action']);actual=C.feedback(step['action'],r)
                assert actual=={k:step[k] for k in actual},'PREFIX_MISMATCH'
                obs,cmds=r.observation,list(r.admissible_commands)
            env.phase='suffix';return env,obs,cmds
        except BaseException:env.close();raise
    def worker(self,code,context,path):
        self.health();d=super().worker(code,context,path)
        if A.read(path)['raw'].get('status') in ('WORKER_ERROR','EVALUATOR_ERROR'):raise RuntimeError('WORKER_INFRASTRUCTURE_ERROR')
        return d
    def branch(self,case,ident,arm,code=None,development=False):
        self.ident=ident
        folder=self.root/ident
        if not (folder/'result.json').exists() and (folder/'start.private.json').exists():raise RuntimeError('PARTIAL_BRANCH_NO_AUTOMATIC_RESTART')
        return super().branch(case,ident,arm,code,development)

def fresh(study,t,i):
    path=study.root/f'native/{i:02d}/case.private.json'
    if path.exists():return A.read(path)
    game=Path(study.p['data_root'])/t['game'];assert A.sha(game)==t['game_sha256'] and A.sha(game.with_name('traj_data.json'))==t['trajectory_sha256']
    env=SelectedTrainEnv(study.p['data_root'],50)
    try:
        with redirect_stdout(io.StringIO()):env.initialize(frozen_game_files=[str(game)]);task,obs,cmds=env.reset()
    finally:env.close()
    bank=SkillLibrary.from_dict(A.read(study.root/'bank.private.json'));layers=bank.retrieve(task.task_type);skills={k:layers[k].to_dict() if layers[k] else None for k in ('exemplar','insight')}
    return A.commit(path,dict(goal=task.goal,initial=dict(observation=obs,commands=list(cmds)),steps=[],task=t,skills=skills,anchor=0))

def collect(root):
    study=Study(root);tasks=A.read(root/'selection.private.json')['tasks'];jobs=[];coverage=[]
    for i,t in enumerate(tasks):
        case=fresh(study,t,i);native=study.branch(case,f'native/{i:02d}','G');steps=native['steps'];placement=C.first_placement(case['goal'],steps);anchors=repeated_retake(case['goal'],steps)
        def add(kind,cp):
            job=dict(game_index=i,kind=kind,checkpoint=cp,checkpoint_sha256=A.digest(cp),label_frozen_before_skill=True)
            jobs.append(job);A.commit(root/f'checkpoints/{i:02d}_{kind}.json',job)
        if placement is not None and placement<50 and not steps[placement-1]['done']:
            normal=dict(case,steps=steps[:placement],anchor=placement);add('NORMAL',normal)
            if i<2:
                valid=[x for x in anchors if x<50 and not steps[x-1]['done']]
                if valid:add('NATURAL_REPEAT_RETAKE',dict(case,steps=steps[:valid[0]],anchor=valid[0]))
                elif placement<49:
                    study.ident=f'controlled/{i:02d}';env,obs,cmds=study.reset(normal)
                    try:
                        m=re.fullmatch(r'You move the (.+?) to the (.+?)\.',normal['steps'][-1]['observation']);action=f'take {m[1]} from {m[2]}'
                        if action in cmds:
                            s=C.feedback(action,env.step(action));add('CONTROLLED_RETAKE',dict(case,steps=normal['steps']+[s],anchor=placement+1))
                        else:A.commit(root/f'controlled/{i:02d}/Unavailable.json',dict(reason='PUBLIC_TAKE_NOT_LEGAL'))
                    finally:env.close()
        coverage.append(dict(game_index=i,task_id=t['task_id'],native_won=native['won'],native_status=native['status'],first_placement=placement,natural_repeat_anchors=anchors,natural_opportunity_observed=bool(anchors),selected_recovery_eligible=i<2))
        print(json.dumps(dict(game=i,native_won=native['won'],checkpoints=[j['kind'] for j in jobs if j['game_index']==i])),flush=True)
    return A.commit(root/'Checkpoints_Frozen.json',dict(jobs=jobs,coverage=coverage,created_at=C.stamp(),candidate_sha256=A.sha(root/'frozen/code.py')))

def paired(root):
    study=Study(root);frozen=A.read(root/'Checkpoints_Frozen.json');code=root/'frozen/code.py';assert A.sha(code)==frozen['candidate_sha256'];results=[]
    for job in frozen['jobs']:
        i=job['game_index'];kind=job['kind'];stem=f'pairs/{i:02d}/{kind}';cp=job['checkpoint'];arms={}
        for arm in (['G','F'] if i%2==0 else ['F','G']):arms[arm]=study.branch(cp,stem+'/'+arm,arm,code if arm=='F' else None)
        assert arms['G']['start_sha256']==arms['F']['start_sha256'],'UNEQUAL_START'
        result=dict(game_index=i,kind=kind,checkpoint_sha256=job['checkpoint_sha256'],arms={a:{k:v[k] for k in ['won','status','suffix_steps','logical_model_calls','worker_calls','policy_actions','policy_errors','first_policy_status','start_sha256']} for a,v in arms.items()})
        A.commit(root/stem/'paired_result.json',result);results.append(result);print(json.dumps(result),flush=True)
    return A.commit(root/'Completed.json',dict(results=results,completed_at=C.stamp(),frozen_candidate_sha256=A.sha(code)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('phase',choices=['collect','paired']);args=parser.parse_args()
    try:globals()[args.phase](args.root.resolve())
    except BaseException as e:A.commit(args.root/f'Stopped_{args.phase}_{int(time.time())}.json',dict(error_type=type(e).__name__,message=str(e),at=C.stamp()));raise
