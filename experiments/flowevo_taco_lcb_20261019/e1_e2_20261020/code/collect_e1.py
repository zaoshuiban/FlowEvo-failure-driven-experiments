"""Offline, sandboxed replay. This script never imports an API client."""
import ast,hashlib,json,pathlib,sys,time,traceback
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(BASE/'repair_v2d_20261020/code'))
from regrade import evaluate,write
from preflight import preflight
from sandbox import Worker

def main():
 policies=json.loads((BASE/'repair_v2d_20261020/policies.json').read_text()); sample=json.loads((ROOT/'sample_frozen.json').read_text())
 for row in sample['selected']:
  tid=row['task_id'];dest=ROOT/'private_e1'/tid
  if (dest/'replay.json').exists():continue
  try:
   taskpath=BASE/'data/tasks'/(tid+'.json');task=json.loads(taskpath.read_text());oldpath=next(BASE.glob('runs/*/'+tid+'/result.json'));old=json.loads(oldpath.read_text());codepath=oldpath.parent/(old['final_stage']+'.py');pre,cases=preflight(task,policies[tid]);verdict=evaluate(task,policies[tid],pre,cases,codepath)
   dest.mkdir(parents=True,exist_ok=True);(dest/'original.py').write_bytes(codepath.read_bytes());(dest/'task.json').write_bytes(taskpath.read_bytes());write(dest/'preflight.json',pre);write(dest/'history.json',old)
   verdict['original_task_sha256']=hashlib.sha256(taskpath.read_bytes()).hexdigest();verdict['sampling_group']=row['sampling_group']
   if 'failed_test_index' in verdict:
    case=next(x for x in cases if x['index']==verdict['failed_test_index']);write(dest/'private_failure_case.json',case)
    with Worker(codepath) as w:
     if not task.get('function_name'):w.call({'mode':'compile_stdio','timeout':6})
     request={'mode':'function' if task.get('function_name') else 'stdio','timeout':6}
     if task.get('function_name'):request.update(function=task['function_name'],args=case['input'])
     else:request['input']=case['input']
     write(dest/'isolated_failure_execution.json',w.call(request))
   write(dest/'replay.json',verdict);print(tid,verdict['status'],flush=True)
  except Exception as exc:write(dest/'collection_error.json',{'error':repr(exc),'traceback':traceback.format_exc()});print('ERROR',tid,repr(exc),flush=True)
if __name__=='__main__':main()
