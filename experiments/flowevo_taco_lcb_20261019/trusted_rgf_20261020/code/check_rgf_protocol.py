import json,pathlib,hashlib
from suite import ROOT

def main():
 frozen=ROOT/'rgf_frozen';m=json.loads((frozen/'manifest.json').read_text());calls=json.loads((frozen/'calls.json').read_text());assert len(calls)==12 and m['independent_failure_tasks']==2
 for tid in {c['task_id'] for c in calls}:
  rows=[c for c in calls if c['task_id']==tid];assert len(rows)==6
  assert {c['condition'] for c in rows}=={'R','G','F'}
  common=[c['request']['messages'][1]['content'].split('\n\nPublic diagnostic, identical in every condition:')[0] for c in rows];assert all(x==common[0] for x in common)
  assert len({json.dumps(c['public_witness'],sort_keys=True) for c in rows})==1
  for c in rows:
   assert c['request']['max_tokens']==32768 and c['request']['temperature']==.2
   assert tid not in c['failure_memory_source_tasks']
   assert bool(c['failure_memory_source_tasks'])==(c['condition']=='F')
   assert not c['own_task_root_cause_disclosed']
  hidden=json.loads((frozen/'hidden'/(tid+'.json')).read_text());assert all(h['input']!=rows[0]['public_witness']['input'] for h in hidden)
  baseline=json.loads((frozen/'baselines'/(tid+'.json')).read_text());assert not baseline['original']['passed'] and baseline['counterfactual']['passed']
 for rel,h in m['hashes'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
 (ROOT/'protocol_checks.json').write_text(json.dumps({'planned_calls':12,'independent_tasks':2,'same_model_parameters':True,'same_public_evidence':True,'F_other_tasks_only':True,'hidden_public_inputs_disjoint':True,'original_fail_and_counterfactual_pass_on_hidden':True,'frozen_hashes_verified':len(m['hashes'])},indent=2));print('RGF protocol isolation and baseline checks PASS')
if __name__=='__main__':main()
