"""Zero API host review tooling. Template is NOT approval or model evidence."""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
from failure_evo.math_gate_pool import SealedGateProvider,review_signature_message,review_version
from failure_evo.math_stream import read,save,sha
from failure_evo.evidence import EvidenceStore
from failure_evo.operator_contract import candidate_identity
from code_math.no_gold import PublicMathTask

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['template','validate','blind-packet','signing-message']);p.add_argument('--run',type=Path,required=True);p.add_argument('--arm',choices=['T','F'],required=True);p.add_argument('--artifact',type=Path,required=True);p.add_argument('--cutoff',type=int,required=True);p.add_argument('--review',type=Path);a=p.parse_args()
 plan=read(a.run/'execution_plan.json');refs=plan['cumulative_input_bindings'];tasks=[PublicMathTask.parse(json.loads(l)) for l in Path(refs['tasks']['path']).read_text().splitlines()]
 s=SimpleNamespace(engineering=False,path=a.run,plan=plan,tasks=tasks,lineage=read(refs['lineage']['path']),arms={a.arm:dict(states=EvidenceStore(a.run/a.arm/'task_state.jsonl'))})
 provider=SealedGateProvider(s,a.arm);art=read(a.artifact);target=provider.review_path(art)
 if a.action=='blind-packet':
  print(json.dumps(dict(candidate_version=candidate_identity(art),
   pool_sha256=plan['gate_pool_binding']['sha256'],
   contract=art['contract'],operator_contract=art.get('operator_contract'),
   Development=[dict(task_id=t.task_id,problem=t.problem) for t in tasks[:a.cutoff][-6:]],
   Gate=[dict(task_id=row['task_id'],problem=row['problem']) for row in provider.rows.values()]),
   ensure_ascii=False,indent=2))
 elif a.action=='signing-message':
  if a.review is None:p.error('signing-message requires --review')
  review=read(a.review)
  if 'signature' in review:p.error('supply unsigned review')
  import sys
  sys.stdout.buffer.write(review_signature_message(plan,a.arm,candidate_identity(art),review))
 elif a.action=='template':
  out=target.with_suffix('.template.json')
  if out.exists():raise PermissionError('existing template retained')
  def label(t):return dict(task_id=t,supported=None,parameters=None,reason='REVIEW_REQUIRED',assumption_quotes=[])
  template=dict(version=review_version(art),artifact_sha256=art['code_sha256'],pool_sha256=plan['gate_pool_binding']['sha256'],reviewer=plan['gate_reviewers'][0],review_method='INDEPENDENT_SEMANTIC_REVIEW_BEFORE_EXECUTION',Development=[label(t.task_id) for t in tasks[:a.cutoff][-6:]],Gate=[label(t) for t in provider.rows])
  if 'operator_contract' in art:template['candidate_version']=candidate_identity(art)
  save(out,template)
  print('UNAPPROVED_TEMPLATE',out);print('Review all pool labels before any candidate Gate execution; remove excess Development items if needed, minimum one positive and one negative. Save reviewed file as',target)
 else:
  package=provider(art,a.cutoff);print('REVIEWED_PACKAGE_READY' if package else 'SHADOW_REVIEW_OR_COVERAGE_INSUFFICIENT')
if __name__=='__main__':main()
