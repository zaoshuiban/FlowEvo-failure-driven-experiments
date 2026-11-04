"""Zero API host review tooling. Template is NOT approval or model evidence."""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
from failure_evo.math_gate_pool import SealedGateProvider,VERSION
from failure_evo.math_stream import read,save,sha
from failure_evo.evidence import EvidenceStore
from code_math.no_gold import PublicMathTask

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['template','validate']);p.add_argument('--run',type=Path,required=True);p.add_argument('--arm',choices=['T','F'],required=True);p.add_argument('--artifact',type=Path,required=True);p.add_argument('--cutoff',type=int,required=True);a=p.parse_args()
 plan=read(a.run/'execution_plan.json');refs=plan['cumulative_input_bindings'];tasks=[PublicMathTask.parse(json.loads(l)) for l in Path(refs['tasks']['path']).read_text().splitlines()]
 s=SimpleNamespace(engineering=False,path=a.run,plan=plan,tasks=tasks,lineage=read(refs['lineage']['path']),arms={a.arm:dict(states=EvidenceStore(a.run/a.arm/'task_state.jsonl'))})
 provider=SealedGateProvider(s,a.arm);art=read(a.artifact);target=provider.review_path(art)
 if a.action=='template':
  out=target.with_suffix('.template.json')
  if out.exists():raise PermissionError('existing template retained')
  def label(t):return dict(task_id=t,supported=None,parameters=None,reason='REVIEW_REQUIRED',assumption_quotes=[])
  save(out,dict(version=VERSION,artifact_sha256=art['code_sha256'],pool_sha256=plan['gate_pool_binding']['sha256'],reviewer=plan['gate_reviewers'][0],review_method='INDEPENDENT_SEMANTIC_REVIEW_BEFORE_EXECUTION',Development=[label(t.task_id) for t in tasks[:a.cutoff][-6:]],Gate=[label(t) for t in provider.rows]))
  print('UNAPPROVED_TEMPLATE',out);print('Review all pool labels before any candidate Gate execution; remove excess Development items if needed, minimum one positive and one negative. Save reviewed file as',target)
 else:
  package=provider(art,a.cutoff);print('REVIEWED_PACKAGE_READY' if package else 'SHADOW_REVIEW_OR_COVERAGE_INSUFFICIENT')
if __name__=='__main__':main()
