"""A4 host-only checkpoint construction. No model, skill execution or training export."""
import argparse,fcntl,time
from pathlib import Path
from collections import Counter
import prepare_alfworld_route_a_a1d as D
import prepare_alfworld_a4_checkpoint_plan as P
from failure_evo.runtime import BudgetExhausted
from failure_evo.run_health import RunUnhealthy
from alfworld_.env import AlfWorldEnv
VERSION='a4-host-checkpoint-collection-v2'
def verify_game(data,origin):
 row=origin['row'];base=Path(data).resolve()/'json_2.1.1';path=(Path(data)/row['game']).resolve()
 if row['split'] not in ('train','valid_seen','valid_unseen') or not path.is_relative_to(base/row['split']):raise PermissionError('frozen split mismatch')
 if D.sha(path)!=row['game_sha256'] or D.sha(path.parent/'traj_data.json')!=row['trajectory_sha256']:raise PermissionError('game content drift')
 return path
class CollectionEnv(AlfWorldEnv):
 def __init__(self,data,split,max_steps=50):
  super().__init__(split={'train':'train','valid_seen':'eval_in_distribution','valid_unseen':'eval_out_of_distribution'}[split],alfworld_data=str(data),max_steps=max_steps)
 def _build_config(self):
  c=super()._build_config();c['dataset']['data_path']=str(Path(self.alfworld_data)/'json_2.1.1/train');c['general']['training_method']='dqn';c['rl']={'training':{'max_nb_steps_per_episode':self.max_steps}};return c
LIMITS=dict(games=80,resets=720,environment_steps=36000,wall_seconds=14400,search_steps=28,max_target_visits=4,episode_steps=50,modes=['READY','TARGET_CONFLICT','UNPROCESSED','OTHER_INSTANCE'])
def configure():
 # Only resource parameters on imported collection helpers; no source edits.
 D.LIMITS={**D.LIMITS,**LIMITS};D.previous.LIMITS={**D.previous.LIMITS,**LIMITS}
def freeze(out,preparation):
 if out.exists():raise FileExistsError(out)
 P.prepare(preparation)
 hits=Path('/private/tmp/a4_exposure_hits.txt')
 if not hits.exists() or hits.read_text().strip():raise PermissionError('exposure audit missing or has hits')
 jobs=P.read(preparation/'checkpoint_jobs.private.json')
 parent=P.read(P.RUN/'protocol.json');data=D.read(Path(parent['dataset'])/'protocol.json')['data_root']
 files=[Path(__file__),Path(D.__file__),Path(D.previous.__file__),P.ROOT/'scripts/prepare_alfworld_route_a_training_checkpoints.py',P.ROOT/'FlowEvo/src/alfworld_/route_a_expanded_labels.py',P.ROOT/'FlowEvo/src/alfworld_/route_a_training_labels.py',P.ROOT/'scripts/run_alfworld_python_recovery_feedback.py',P.ROOT/'FlowEvo/src/alfworld_/skill_acquisition.py',P.ROOT/'FlowEvo/src/alfworld_/env.py']
 out.mkdir(parents=True,mode=0o700)
 D.commit(out/'selection.private.json',{'tasks':[dict(task=j['task'],stratum=j['stratum'],role='INDEPENDENT_TEST') for j in jobs]})
 D.commit(out/'exposure_audit.json',dict(scope='all *.jsonl under repository runs and ~/.local/share/flowevo; frozen game SHA exact search',hits=[],checked_at=time.time(),limitation='does not certify unrecorded external activity'))
 return D.commit(out/'protocol.json',dict(version=VERSION,limits=LIMITS,data_root=data,environment=D.environment_manifest(data),selection_sha256=D.sha(out/'selection.private.json'),files={str(p.resolve()):D.sha(p) for p in files},preparation_sha256=D.sha(preparation/'A4_Preparation_Protocol.json'),scope='HOST_REFERENCE_ONLY_NOT_SKILL_EVALUATION',paid_requests_allowed=0,worker_calls_allowed=0,candidate_execution_allowed=False,label_rules='UNCHANGED_A1d_WITH_INDEPENDENT_TEST_ROLE',retention_gate='NOT_REQUIRED_FOR_HOST_COLLECTION_REQUIRED_BEFORE_CANDIDATE_EVALUATION'))
def verify(out):
 p=D.read(out/'protocol.json');s=D.read(out/'selection.private.json')
 if p['version']!=VERSION or p['limits']!=LIMITS or D.sha(out/'selection.private.json')!=p['selection_sha256']:raise PermissionError('freeze drift')
 if any(D.sha(f)!=h for f,h in p['files'].items()):raise PermissionError('source drift')
 if D.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('environment drift')
 if len(s['tasks'])!=80 or any(r['role']!='INDEPENDENT_TEST' for r in s['tasks']):raise PermissionError('roles')
 for r in s['tasks']:verify_game(p['data_root'],dict(row=r['task']))
 return p,s

def probe(out):
 configure();plan,selection=verify(out)
 with (out/'collection.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  events=D.EvidenceStore(out/'collection.jsonl');old=events.records()
  starts={e['payload']['id'] for e in old if e['kind']=='GAME_STARTED'};done={e['payload']['id']:e['payload'] for e in old if e['kind']=='GAME_COMPLETED'}
  if starts!=set(done):raise RunUnhealthy('unfinished game requires audit; no automatic replay')
  receipts=D.EnvironmentReceipts(out/'environment.jsonl',LIMITS['environment_steps'])
  if not old:events.append('RUN_STARTED',dict(protocol_sha256=D.fingerprint(plan)),time.time())
  deadline=events.records()[0]['at']+LIMITS['wall_seconds']
  for i,row in enumerate(selection['tasks']):
   tid=row['task']['task_id'];path=out/'games'/f'{tid}.private.json'
   if tid in done:
    if D.sha(path)!=done[tid]['sha256']:raise PermissionError('receipt drift')
    continue
   if time.time()>deadline:raise BudgetExhausted('collection wall limit')
   events.append('GAME_STARTED',dict(id=tid,index=i),time.time());env=CollectionEnv(plan['data_root'],row['task']['split'],max_steps=50)
   try:
    env.initialize(frozen_game_files=[str(verify_game(plan['data_root'],dict(row=row['task'])))])
    p,goal,initial=D.previous.start(env,row['task'],receipts,events,tid+'/search',deadline)
    subject,error=D.previous.find_subject(p,goal);origin=dict(row=row['task'],goal=goal,initial=initial,steps=list(p.history));branches=[]
    if not error:
     for mode in LIMITS['modes']:
      try:b=D.collect(plan,row,env,origin,subject,mode,receipts,events,deadline)
      except BudgetExhausted as e:
       if str(e)!='episode exhausted':raise
       b=dict(status='NOT_CONSTRUCTED',reason='EPISODE_LIMIT',branch=tid+'/'+mode)
      b['mode']=mode
      if b['status']=='COLLECTED':
       b['execution_receipt_sha256']=D.fingerprint([e['record_hash'] for e in events.records() if e['kind']=='TRANSITION' and e['payload']['branch']==b['branch']])
       b.update(D.previous.replay(env,row,b,receipts,events,deadline))
      branches.append(b)
    D.commit(path,dict(task=row['task'],role=row['role'],stratum=row['stratum'],origin=origin,search_error=error,branches=branches))
    events.append('GAME_COMPLETED',dict(id=tid,sha256=D.sha(path)),time.time());print(i+1,tid,error or dict(Counter(b['status'] for b in branches)),flush=True)
   finally:env.close()
  if (out/'collection_summary.json').exists():return D.read(out/'collection_summary.json')
  return D.commit(out/'collection_summary.json',dict(games=80,environment_steps=sum(receipts.started.values()),resets=sum(e['kind']=='RESET_CONFIRMED' for e in events.records()),paid_requests=0,candidate_executions=0,elapsed_seconds=time.time()-events.records()[0]['at']))

def audit(out):
 plan,sel=verify(out);events=D.EvidenceStore(out/'collection.jsonl').records();D.EnvironmentReceipts(out/'environment.jsonl',LIMITS['environment_steps'])
 complete={e['payload']['id']:e['payload']['sha256'] for e in events if e['kind']=='GAME_COMPLETED'}
 if len(complete)!=80:raise RunUnhealthy('incomplete collection')
 samples=[];unresolved=[]
 for r in sel['tasks']:
  path=out/'games'/f"{r['task']['task_id']}.private.json"
  if D.sha(path)!=complete[r['task']['task_id']]:raise PermissionError('receipt drift')
  g=D.read(path);valid=[]
  for b in g['branches']:
   if b['status']!='COLLECTED':unresolved.append(dict(game=r['task']['task_id'],stratum=r['stratum'],**b));continue
   expected=b['prefix']+[b['failure']]+b['recovery_probe'];actual=[e for e in events if e['kind']=='TRANSITION' and e['payload']['branch']==b['branch']];replay=[e['payload']['after'] for e in events if e['kind']=='TRANSITION' and e['payload']['branch']==b['branch']+'/verification']
   if [e['payload']['after'] for e in actual]!=expected or replay!=expected or D.fingerprint(expected)!=b['replay_sha256'] or D.fingerprint([e['record_hash'] for e in actual])!=b['execution_receipt_sha256']:raise PermissionError('unverified branch')
   valid.append(b)
  positives=[b for b in valid if D.inherited_review(b)['label']=='MATCH']
  for b in valid:
   same=[p for p in positives if D.command(p['failure']['action'])[1][0]==D.command(b['failure']['action'])[1][0]]
   label=D.inherited_review(dict(b,positive_witness=dict(verified=bool(same),same_subject=bool(same),won=bool(same))))
   common=dict(game_sha256=r['task']['game_sha256'],scene_id=r['task']['scene'],role='INDEPENDENT_TEST',stratum=r['stratum'],physical_state_group_id=D.fingerprint([r['task']['game_sha256'],b['prefix']]),source_receipt_sha256=D.sha(path),source_key=b['branch'])
   sample=dict(common,**label,sample_id='a4/'+b['branch']+'/full',candidate_context=D.context(b['original_goal'],b['prefix']+[b['failure']]))
   if label['label'] is None:unresolved.append(sample);continue
   samples.append(sample)
   if b['mode']=='READY' and D.goal_parts(b['original_goal'])[2]:samples.extend(dict(common,**v,sample_id='a4/'+b['branch']+f'/view{i}') for i,v in enumerate(D.matched_views(b,label)))
  if g['search_error']:unresolved.append(dict(game=r['task']['task_id'],stratum=r['stratum'],reason=g['search_error']))
 D.commit(out/'review.private.json',dict(samples=samples,unresolved=unresolved))
 return D.commit(out/'checkpoint_manifest.json',dict(status='CHECKPOINTS_FROZEN_NOT_CANDIDATE_EVALUATED',protocol_sha256=D.fingerprint(plan),review_sha256=D.sha(out/'review.private.json'),coverage={s:dict(records=len(rs),labels=dict(Counter(x['label'] for x in rs)),games=len({x['game_sha256'] for x in rs}),scenes=len({x['scene_id'] for x in rs}),physical_groups=len({x['physical_state_group_id'] for x in rs})) for s in ['strict_scene','expanded_game_group'] for rs in [[x for x in samples if x['stratum']==s]]},unresolved=len(unresolved),paid_requests=0,candidate_executions=0,training_export_allowed=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','verify','probe','audit']);p.add_argument('--output',type=Path,required=True);p.add_argument('--preparation',type=Path,default=P.ROOT/'runs/alfworld_a4_preparation_20261115_01');a=p.parse_args()
 result=freeze(a.output.resolve(),a.preparation.resolve()) if a.command=='freeze' else globals()[a.command](a.output.resolve());print(D.canonical(result if a.command=='audit' else {'command':a.command,'completed':True}))
