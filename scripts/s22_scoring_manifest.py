"""Evaluator-side metadata only. Never exports sealed inputs/answers into model wires."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'reports/s22_action_preference_v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=ROOT/'runs/s20_preparation_20261025_01/sealed_final_tasks.json'
 # Only already-used TACO80/S18/S15 evaluator archives; never external confirmation pool.
 data=json.loads(source.read_text());byid={r['task_id']:dict(cases=r['cases'],source_ref=str(source.relative_to(ROOT))) for r in data};rows=[]
 extra=ROOT/'runs/s18_data_freeze_20261023_01/evaluator_only.json'
 for tid,r in json.loads(extra.read_text()).items():byid[tid]=dict(cases=r['audit_cases'],source_ref=str(extra.relative_to(ROOT)))
 legacy=ROOT/'runs/s15_learn_reuse30_20261022_01/tasks.json'
 for r in json.loads(legacy.read_text()):
  if r['task_id']=='taco_0313':byid[r['task_id']]=dict(cases=r['audit_cases'],source_ref=str(legacy.relative_to(ROOT)))
 for path in sorted((OUT/'frozen').glob('*.json')):
  record=json.loads(path.read_text());p=record['public_checkpoint'];entry=byid.get(p['task_id'])
  cases=entry['cases'] if entry else [];public_inputs={c['input'].strip() for c in p['public_cases']}
  overlap=sum(c['input'].strip() in public_inputs for c in cases)
  rows.append(dict(evaluator_ref=entry['source_ref'] if entry else None,task_id=p['task_id'],candidate_file=str(path.relative_to(ROOT)),candidate_file_sha256=sha(path),public_case_count=len(p['public_cases']),public_cases_sha256=hashlib.sha256(json.dumps(p['public_cases'],sort_keys=True).encode()).hexdigest(),sealed_case_count=len(cases),public_sealed_overlap=overlap,review_available=bool(cases) and not overlap,reason='FROZEN_DEVELOPMENT_REVIEW_AVAILABLE' if cases and not overlap else 'NO_BOUND_SEPARATE_REVIEW' if not cases else 'TEST_ROLE_OVERLAP',scoring_role='previously exposed same-task final review, not new independent holdout'))
 out=dict(evaluator_sources={str(p.relative_to(ROOT)):sha(p) for p in [source,extra,legacy]},sealed_contents_exported=False,confirmation119_accessed=False,selection_basis='evaluation availability only; no target model outputs or scores',rows=rows)
 (OUT/'scoring_manifest.json').write_text(json.dumps(out,indent=2)+'\n');print([(x['task_id'],x['sealed_case_count'],x['public_sealed_overlap']) for x in rows])
if __name__=='__main__':main()
