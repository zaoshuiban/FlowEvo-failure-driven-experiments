"""Metadata-only A4 preparation. No model, environment reset, or candidate execution."""
import argparse,json,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/alfworld_route_a_a3b_semantic_feedback_20261114_01/pilot_frozen'
OLD=ROOT/'runs/alfworld_route_a_a3_launch_check_20261114_01/A4_PreOutcome_Rules.json'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def commit(p,data):
 p=Path(p);s=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
 if p.exists():
  if p.read_text()!=s:raise ValueError('immutable output differs: '+str(p))
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def validate_jobs(jobs,training):
 ids=[j['task']['game_sha256'] for j in jobs]
 if len(ids)!=80 or len(set(ids))!=80:raise ValueError('pool cardinality')
 if set(ids)&{r['game_sha256'] for rs in training.values() for r in rs}:raise ValueError('training overlap')
 if any(j['label'] is not None or j['status']!='NOT_CONSTRUCTED' for j in jobs):raise ValueError('metadata cannot establish a label')
def prepare(output):
 old=read(OLD);pool=read(old['pool_path']);assert sha(old['pool_path'])==old['pool_sha256']
 final=read(RUN/'Final_Candidate_Freeze.json');result=read(RUN/'result.json');plan=read(RUN/'protocol.json')
 assert final['selected']==result['selection']['selected'] and final['permission']=='SHADOW'
 assert not final['publication_authorized'] and not final['A4_authorized']
 assert sha(RUN/'frozen_candidate/gate.py')==final['source_sha256']
 for p,h in {**plan['historical_sha256'],**plan['code_sha256']}.items():assert sha(p)==h,p
 sources={'S0':ROOT/'runs/python_recovery_decline_revision_20261112_01/candidate_0/revision_02/decoded.py',
 'S1':ROOT/'runs/alfworld_container_boundary_learning_20261113_02/candidate_0/applicability/gate.py',
 'Rule':ROOT/'FlowEvo/src/alfworld_/recovery_applicability_rule.py','A3b_candidate_0':RUN/'frozen_candidate/gate.py'}
 assert sha(sources['S0'])=='233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37'
 data_root=Path(read(Path(plan['dataset'])/'protocol.json')['data_root'])
 jobs=[]
 for stratum in ['strict_scene','expanded_game_group']:
  assert [x['game_sha256'] for x in pool[stratum]]==old['game_order'][stratum]
  for t in pool[stratum]:
   assert sha(data_root/t['game'])==t['game_sha256']
   assert sha((data_root/t['game']).with_name('traj_data.json'))==t['trajectory_sha256']
   jobs.append(dict(order=len(jobs),stratum=stratum,task=t,modes=old['checkpoint_construction']['modes'],status='NOT_CONSTRUCTED',label=None))
 roles=read(RUN/'roles.private.json');validate_jobs(jobs,roles)
 training_groups=set();training_scenes={x['scene_id'] for rs in roles.values() for x in rs}
 for p in [ROOT/'runs/alfworld_route_a_a1c_20261113_01/selection.private.json',ROOT/'runs/alfworld_route_a_a1d_20261113_01/selection.private.json']:
  for r in read(p)['tasks']:training_groups.add(r['task']['group'])
 assert not training_groups&{j['task']['group'] for j in jobs}
 assert not training_scenes&{j['task']['scene'] for j in jobs if j['stratum']=='strict_scene'}
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 arms={}
 for name,source in sources.items():
  dest=output/'frozen_sources'/f'{name}.py';dest.parent.mkdir(exist_ok=True)
  if dest.exists():assert sha(dest)==sha(source)
  else:dest.write_bytes(source.read_bytes())
  arms[name]=dict(original_path=str(source),sha256=sha(source),snapshot=str(dest.resolve()),permission='OFFLINE_EVALUATION_ONLY_NOT_RELEASED')
 commit(output/'Candidate_Freeze.json',dict(selected=final,original_result_sha256=sha(RUN/'result.json'),training_scores=result['attempts'][0]['train'],validation_scores=result['attempts'][0]['validation'],selection=result['selection'],arms=arms))
 commit(output/'checkpoint_jobs.private.json',jobs)
 protocol=dict(version='a4-preparation-v2-20261115',status='PREPARATION_ONLY_NOT_EXECUTABLE_A4',previous_rules_sha256=sha(OLD),pool_sha256=sha(old['pool_path']),
  candidate_freeze_sha256=sha(output/'Candidate_Freeze.json'),jobs_sha256=sha(output/'checkpoint_jobs.private.json'),arms=arms,
  changes=['Use frozen A3b candidate_0 instead of old A3 winner','Add archival S1 comparison','Keep original retention veto pending; no candidate replacement'],
  construction=old['checkpoint_construction'],annotation=old['annotation'],comparison=dict(old['comparison'],arms=list(arms)),
  construction_no_candidate_or_rule_decisions=True,retention_status='PENDING_NOT_WAIVED',paid_api_authorized=False,independent_games_executed=0,
  prerequisites=['freeze and test a separate A4 collection entry; do not run the old training collector on sealed games','fresh project-wide executed-exposure audit before environment reset','freeze resource/Worker/environment and recovery semantics','construct and independently review checkpoints before evaluating candidates','complete the existing exposed retention veto without reselection'],
  reporting='strict 34 primary, expanded 46 secondary; group by game and physical checkpoint; labels unresolved are unscored')
 commit(output/'A4_Preparation_Protocol.json',protocol)
 summary=dict(status=protocol['status'],protocol_sha256=sha(output/'A4_Preparation_Protocol.json'),games=len(jobs),
  strata={s:dict(games=sum(j['stratum']==s for j in jobs),scenes=len({j['task']['scene'] for j in jobs if j['stratum']==s})) for s in old['game_order']},
  labels_verified=0,checkpoints_constructed=0,paid_requests=0,training_game_and_group_overlap=0,source_hash_checks='PASS',candidate_unchanged=True,
  note='Metadata and A3b training isolation checked; historical inventory is not a fresh comprehensive exposure proof.')
 commit(output/'Preparation_Audit.json',summary);return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.output.resolve()),ensure_ascii=False))
