"""Single-use isolated evaluation, not registry admission. No learning after any score."""
import json,sys,time,collections
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.semantic_contract import SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from code_math.no_gold import PublicMathTask

def load(p):return json.loads(p.read_text())
def evaluate(out):
 if not (out/'GENERATION_COMPLETE.json').exists():raise RuntimeError('freeze generated candidates before evaluation')
 plan=load(out/'protocol.json');data=out/plan['data'];manifest=load(data/'manifest.json');assert sha(data/'manifest.json')==plan['data_manifest_sha256'];assert all(sha(data/p)==h for p,h in manifest['files'].items())
 if (out/'candidate_freeze.json').exists():raise RuntimeError('evaluation consumed')
 candidates={'V31_F3_F':manifest['old_artifact']}
 for key in plan['order']:
  p=out/key/'artifact.json'
  if p.exists():candidates[key]=load(p)
 assert all(a['solver_sha256']==plan['algorithm_sha256'] for a in candidates.values())
 save(out/'candidate_freeze.json',dict(at=time.time(),artifacts=candidates,eligible_for_evaluation='static-valid, all included before outcomes',experimental=0))
 for role in ['development','gate']:
  d=out/role;tasks=load(data/'public'/f'{role}.json');results=[];runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),d/'worker.jsonl')
  for key,a in candidates.items():
   for t in tasks:
    r=runner.run(a,PublicMathTask.parse(t));results.append(dict(candidate=key,task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),observation=r))
   print(role,key,'executed',flush=True)
  save(d/'outputs_locked.json',results);save(d/'lock.json',dict(sha256=sha(d/'outputs_locked.json'),at=time.time()))
  # Gold first accessed after entire role output lock. No model requests after generation phase.
  from code_math.private_math_scoring import normalized
  private={r['task_id']:r for r in load(data/'private'/f'{role}.json')}
  for r in results:
   p=private[r['task_id']];o=r['observation'];m=o['match'];assert p['problem_sha256']==r['problem_sha256'];r['supported']=p['supported'];r['correct']=None;r['parameter_match']=None
   if o['status']=='APPLIED' and p['supported'] is True:
    r['correct']=normalized(o['answer'])==normalized(p['answer']);r['parameter_match']=m.get('parameters')==p['parameters']
   r['correct_accept']=p['supported'] is True and m['status']=='MATCH' and r['correct'] is True
   r['false_accept']=p['supported'] is False and m['status']=='MATCH' and o['status']=='APPLIED'
   r['ambiguous_accept']=p['supported'] is None and m['status']=='MATCH'
   r['interface_error']=m['status']=='ERROR';r['execution_error']=o['status']=='ERROR' and m['status']!='ERROR'
  save(d/'scores.json',results)
  summary={}
  for key in candidates:
   rs=[r for r in results if r['candidate']==key];pos=sum(r['supported'] is True for r in rs);neg=sum(r['supported'] is False for r in rs);dec=pos+neg
   summary[key]=dict(total=len(rs),supported=pos,unsupported=neg,ambiguous=len(rs)-dec,correct_accept=sum(r['correct_accept'] for r in rs),false_accept=sum(r['false_accept'] for r in rs),unknown=sum(r['supported'] is not None and r['observation']['match']['status']=='UNKNOWN' for r in rs),interface_error=sum(r['interface_error'] for r in rs),execution_error=sum(r['execution_error'] for r in rs),ambiguous_accept=sum(r['ambiguous_accept'] for r in rs),parameter_mismatch=sum(r['parameter_match'] is False for r in rs))
  save(d/'summary.json',summary)
  # No callback to compiler; gate cannot revise/select a replacement.
 save(out/'COMPLETE.json',dict(no_post_evaluation_generation=True,gate_once=True,experimental=0,algorithm_unchanged=all(sha(a['solver_path'])==plan['algorithm_sha256'] for a in candidates.values())))
if __name__=='__main__':evaluate(Path(sys.argv[1]).resolve())
