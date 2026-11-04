"""Audit the synthetic run without changing frozen data or learner."""
import json
import audit_math_auto100 as common
from run_math_synthetic100 import OUT
from failure_evo.evidence import EvidenceStore
from failure_evo.contracts import fingerprint

def main():
 common.OUT=OUT;common.main()
 roles=json.loads((OUT/'roles.json').read_text());selected=json.loads((OUT/'selected_bundle.json').read_text());questions=[{'problem':e['task']['problem']} for e in selected['events']]
 flags={}
 for arm in ['T','F']:
  path=OUT/arm/'provider.jsonl';ev=EvidenceStore(path).records()
  wire=next(x['payload']['wire'] for x in ev if x['kind']=='SEND_STARTED');payload=json.loads(wire['messages'][1]['content']);evidence=payload['evidence']
  assert evidence['questions']==questions
  assert ('observations' in evidence)==(arm=='F')
  assert set(payload)=={'protocol','evidence'}
  if arm=='F':
   assert all(e['terminal_status']=='CONFIRMED_WRONG' for e in evidence['observations'])
   assert all(e['origin']=='DEEPSEEK' and e['correct'] is False and e['available_after_sequence']<20 for e in selected['events'])
  flags[arm]=dict(exact_source_questions=True,has_failure_trajectory='observations' in evidence,selection_failure_membership_hint_visible='failures' in evidence['selection'],gold_exposed=False)
 assert len(json.loads((OUT/'oracle_acceptance.json').read_text()))==100
 (OUT/'generation_visibility_audit.json').write_text(json.dumps({'passed':True,'arms':flags,'limitation':'T is blind to wrong trajectories, not source-failure-selection metadata'},ensure_ascii=False,indent=2)+'\n')
 print('synthetic generation visibility and actual request audit passed')
if __name__=='__main__':main()
