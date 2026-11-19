from pathlib import Path
import sys,json,io,hashlib
from contextlib import redirect_stdout
root=Path('/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments');sys.path[:0]=[str(root/'scripts'),str(root/'FlowEvo/src')]
from alfworld_revision_environment import SelectedTrainEnv
import run_alfworld_route_c_bounded_learning as C
from alfworld_route_d_interface import public_state,canonical
run=root/'runs/alfworld_route_d_20261118_01';m=json.loads((run/'Preparation_Manifest.json').read_text());case=json.loads((run/'checkpoint.private.json').read_text());p=m['old_protocol'];t=case['task'];game=Path(p['data_root'])/t['game']
assert C.A.sha(game)==t['game_sha256'] and C.A.sha(game.with_name('traj_data.json'))==t['trajectory_sha256']
receipts=[];env=SelectedTrainEnv(p['data_root'],50)
try:
 with redirect_stdout(io.StringIO()):env.initialize(frozen_game_files=[str(game)]);task,obs,cmds=env.reset()
 assert task.goal==case['goal'] and obs==case['initial']['observation'] and list(cmds)==case['initial']['commands']
 for i,s in enumerate(case['steps'],1):
  assert s['action'] in cmds
  f=run/'P0_replay.jsonl'
  with f.open('a') as out:out.write(canonical(dict(kind='STARTED',step=i,action=s['action']))+'\n');out.flush()
  r=env.step(s['action']);actual=C.feedback(s['action'],r)
  with f.open('a') as out:out.write(canonical(dict(kind='RETURNED',step=i,feedback=actual))+'\n');out.flush()
  assert actual=={k:s[k] for k in actual},f'prefix mismatch {i}'
  receipts.append(actual);cmds=list(r.admissible_commands)
 assert len(receipts)==16
 result=dict(passed=True,prefix_actions=16,recovery_actions=0,API_requests=0,checkpoint_public_hash=m['initial_public_context_sha256'],exact_step_receipts=True)
finally:env.close()
(run/'P0_Replay_Result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
