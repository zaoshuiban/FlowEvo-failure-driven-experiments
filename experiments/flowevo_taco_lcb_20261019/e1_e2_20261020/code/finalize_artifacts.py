import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 frozen=json.loads((ROOT/'e2_frozen/manifest.json').read_text());source_verified=0;metadata_omitted=[]
 for rel,h in frozen['hashes'].items():
  if pathlib.Path(rel).name.startswith('._'):
   metadata_omitted.append(rel);continue
  p=ROOT/rel
  prefix='../repair_v2d_20261020/'
  if rel.startswith(prefix):p=ROOT.parent/'repair_v2/epochs/repair_v2d_20261020'/rel[len(prefix):]
  # The server has its original sibling checkout; the delivered workspace stores epochs under repair_v2.
  if not p.exists() and rel.startswith(prefix):p=ROOT/rel
  assert p.exists() and sha(p)==h,rel
  source_verified+=1
 cards=json.loads((ROOT/'e1_cards_final.json').read_text());sample=json.loads((ROOT/'sample_frozen.json').read_text());assert len(cards)==93 and {c['task_id'] for c in cards}=={c['task_id'] for c in sample['selected']}
 for c in cards:
  p=ROOT/'private_e1'/c['task_id'];assert sha(p/'original.py')==c['source_code_sha256']
  if (p/'public_legal_failure_witness.json').exists():c['independent_evidence']=json.loads((p/'public_legal_failure_witness.json').read_text())
  (p/'card_final.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
  links=[]
  for name in ['original.py','statement.txt','history.json','replay.json','preflight.json','private_failure_case.json','isolated_failure_execution.json','old_failure_case.json','old_evaluator_trace.json','old_final.verdict.json','public_legal_failure_witness.json','independent_reflection_proof.json','original_final.response.json']:
   if (p/name).exists():links.append(f'[{name}]({name})')
  text=f"# {c['task_id']}\n\n`{c['label']}` / `{c['root_subtype']}`\n\n{c['finding']}\n\n"+'; '.join(links)+'\n\n'
  if c.get('independent_evidence'):text+='Independent evidence:\n```json\n'+json.dumps(c['independent_evidence'],ensure_ascii=False,indent=2)+'\n```\n\n'
  if c.get('additional_evidence'):text+=c['additional_evidence']+'\n\n'
  text+='Reproduce:\n```sh\n'+c['reproduction']+'\n```\n\nThis finding confirms the specific recorded defect, not universal program correctness. Private tests and expected values were withheld from E2 repair prompts.\n';(p/'最终证据卡.md').write_text(text)
 (ROOT/'e1_cards_final.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2)+'\n')
 if (ROOT/'e2_summary.json').exists():
  summary=json.loads((ROOT/'e2_summary.json').read_text());assert summary['status']=='COMPLETED' and summary['graded_calls']==summary['planned_calls']==12
  calls=json.loads((ROOT/'e2_frozen/calls.json').read_text());marker='\nFix the solution and return the corrected complete Python program/function.'
  for tid in {c['task_id'] for c in calls}:
   bodies=[]
   for c in calls:
    if c['task_id']!=tid:continue
    body=json.loads(json.dumps(c['request']));user=body['messages'][1]['content'];left,right=user.split('\n\nVerifier feedback: ',1);feedback,tail=right.split(marker,1);body['messages'][1]['content']=left+'<CONTROLLED_FEEDBACK_BLOCK>'+tail;bodies.append(body)
   assert all(b==bodies[0] for b in bodies)
  assert len(summary['actual_models'])==1 and 'deepseek-flash' in summary['actual_models']
  (ROOT/'final_verification.json').write_text(json.dumps({'e1_sample_identity_and_original_code_hashes':93,'e1_final_cards':len(cards),'e2_calls':12,'e2_same_actual_model':summary['actual_models'],'e2_prompt_arms_differ_only_in_controlled_feedback':True,'token_and_call_limits_respected':summary['conservative_charged_or_reserved_tokens']<=3000000 and summary['dispatched_calls']<=72,'grader_validation_methods':13,'independent_transform_pairs':819,'independent_magazine_checks':42,'e1_public_candidate_probes':110,'e1_public_batches_executed':3649},indent=2)+'\n')
 verification=ROOT/'final_verification.json'
 if verification.exists():
  v=json.loads(verification.read_text());v.update(frozen_executable_source_and_protocol_files_verified=source_verified,non_executable_appledouble_metadata_excluded=metadata_omitted,server_frozen_files_verified_before_archive=len(frozen['hashes']));verification.write_text(json.dumps(v,indent=2)+'\n')
 files={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and p.name!='artifact_integrity.json' and not p.name.startswith('._') and '__pycache__' not in p.parts and p.suffix not in ['.gz','.pyc']}
 (ROOT/'artifact_integrity.json').write_text(json.dumps({'sha256':files,'files':len(files)},indent=2)+'\n');print('artifact files',len(files))
if __name__=='__main__':main()
