"""Zero-API paired design inventory. Does not authorize or launch model calls."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/math_goal_consistency_20261102/ab_design'
PARENT=ROOT/'runs/math_symmetric_repair_20261031_01'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def textsha(s):return hashlib.sha256(' '.join(s.split()).encode()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=False)
 source=load(ROOT/'reports/math_goal_consistency_20261102/preparation_manifest.json')
 blocks=[]
 for i,a in enumerate(source['candidates']):
  path=Path(a['source_path']);assert sha(path)==a['source_sha256']
  block=dict(block_id=f'algorithm-{i:02d}',historical_artifact=a['candidate'],algorithm_path=str(path),algorithm_sha256=sha(path),
   historical_arm_is_not_new_treatment=True,new_arms=[dict(arm=x,algorithm_sha256=sha(path),contract_status='NOT_GENERATED') for x in ('T_new','F_new')],
   shared_parser_status='NOT_FROZEN',shared_capability_declaration_status='NOT_GENERATED',contract_replications=1)
  blocks.append(block)
 exposed=[]
 for role,rows in load(PARENT/'private_development.json').items():
  for r in rows:exposed.append(dict(task_id=r['task_id'],problem_sha256=textsha(r['problem']),role='EXPOSED_DEVELOPMENT',source_role=role))
 for r in load(PARENT/'independent_gate/private_cases.json'):
  exposed.append(dict(task_id=r['task_id'],problem_sha256=textsha(r['problem']),role='EXPOSED_OLD_GATE',source_role='Gate'))
 result=dict(version='goal-consistency-ab-design-v1',status='DESIGN_FROZEN_DATA_NOT_READY',
  objectives={'A':'fixed algorithm old versus new semantic pipeline; no computational revision',
              'B':'within identical algorithm paired T_new versus F_new contracts; conditional incremental effect of additional failure evidence'},
  blocks=blocks,exposed_local_cases=exposed,
  old_gate_exposed_count=sum(x['role']=='EXPOSED_OLD_GATE' for x in exposed),
  expected_new_contracts=12,model_calls=0,
  required_before_execution=['complete historical exposure/lineage registry including V3',
   'new development and confirmation sets, independently reviewed semantic labels',
   'failure evidence cutoff and no source lineage crossing confirmation',
   'shared vocabulary/declaration/parser and mapping frozen, approved model and budget',
   'paired prompts/resource limits and role isolation zero API acceptance'],
  confirmation_tasks=[],development_tasks=[],cross_original_status='NOT_ESTABLISHED',
  independent_algorithms=False,scope='six artifacts from one mechanism; not six independent mathematical families',
  permission='NO_PAID_RUN_OR_PUBLICATION_AUTHORIZATION')
 (OUT/'paired_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 checks=dict(six_blocks=len(blocks)==6,twelve_contracts=sum(len(b['new_arms']) for b in blocks)==12,
   identical_algorithm_within_pair=all(len({a['algorithm_sha256'] for a in b['new_arms']})==1 for b in blocks),
   all_historical_gate_exposed=result['old_gate_exposed_count']==26,
   no_confirmation_relabeling=result['confirmation_tasks']==[],no_paid_calls=result['model_calls']==0)
 assert all(checks.values())
 (OUT/'design_checks.json').write_text(json.dumps(checks,indent=2))
 print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
