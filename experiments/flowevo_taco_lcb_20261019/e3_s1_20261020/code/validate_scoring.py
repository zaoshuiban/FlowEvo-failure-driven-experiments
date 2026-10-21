"""Positive consistency and deliberately wrong checker probes; not failure learning data."""
from replay import R,B,read,write,evaluate
def main():
 manifest=read(R/'review_manifest.json');suite=read(R/'public_suite.json')['cases'];rows=[];extra_exec=0
 for t in manifest['tasks']:
  tid=t['task_id'];task=read(R/'source/tasks'/(tid+'.json'));selected=None
  for a in t['historical_programs']:
   v=read(R/'verdicts'/tid/(a['stage']+'.json'));p=R/'stress_verdicts_v2'/tid/(a['stage']+'.json')
   if v['passed'] and (not p.exists() or read(p)['passed']):selected={'source':'historical consistency witness, not full-domain certification','stage':a['stage'],'source_path':a['source_path']};break
  if selected is None:
   assert tid=='lcb_atcoder_abc399_e'
   source=B/'trusted_rgf_20261020/validated_references'/(tid+'.py');v=evaluate(tid,source,suite[tid]);assert v['passed'];extra_exec+=v['executions'];selected={'source':'PREEXISTING_E2_R2_REFERENCE_NOT_HISTORICAL_2132','source_path':str(source),'status':v['status'],'tests':v['tests_passed']}
  fn=task.get('function_name');wrong=(f'def {fn}(*args):\n    return {{"deliberate_wrong_fixture": True}}\n' if fn else 'print("__DELIBERATELY_WRONG_FIXTURE__")\n');p=R/'acceptance/wrong_fixtures'/(tid+'.py');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(wrong);v=evaluate(tid,p,suite[tid][:1],fn);assert not v['passed'] and v['status']=='WRONG_ANSWER';extra_exec+=v['executions'];rows.append({'task_id':tid,'positive_consistency_witness':selected,'wrong_fixture_rejected':True,'wrong_fixture_synthetic':True})
 write(R/'scoring_validation.json',{'status':'PASS','tasks':len(rows),'positive_consistency_witnesses':len(rows),'synthetic_wrong_fixtures_rejected':len(rows),'extra_sandbox_test_executions':extra_exec,'new_model_calls':0,'rows':rows,'limitation':'agreement on finite legal suite is not global correctness; synthetic probes never enter historical mechanism support'})
 print('SCORING VALIDATION PASS',len(rows),'positive witnesses;',len(rows),'wrong fixtures rejected',flush=True)
if __name__=='__main__':main()
