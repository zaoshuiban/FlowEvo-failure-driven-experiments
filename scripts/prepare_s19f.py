"""S19-F zero-API scorer acceptance; never constructs a model sender."""
import argparse,copy,json,subprocess,tempfile,time
from pathlib import Path
import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.contracts import strict_stream_task,fingerprint

BASE='cedf3e57e0a55fb2bb78d4d41e3d0ba6daf719e0'
def main(bundle,output):
 bundle=Path(bundle).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
 p=e.read(bundle/'plan_proposal.json');tasks=e.read(bundle/'tasks.json');manifest=e.read(bundle/'task_manifest.json')
 if e.sha(bundle/'tasks.json')!=p['tasks_sha256']:raise ValueError('task hash changed')
 for file,h in p['frozen_files'].items():
  if e.sha(e.ROOT/file)!=h:raise ValueError('frozen dependency changed: '+file)
 for file in p['frozen_files']:
  if file.startswith('FlowEvo/src/failure_evo/') or file in ('scripts/run_learning_stream.py','scripts/run_workflow_v2.py'):
   frozen=subprocess.check_output(['git','show',BASE+':'+file],cwd=e.ROOT)
   if frozen!=(e.ROOT/file).read_bytes():raise ValueError('mechanism differs from requested commit')
 configure_worker(p['worker_environment']);(out/'tmp').mkdir();tempfile.tempdir=str(out/'tmp')
 budget=e.PersistentBudget(out/'acceptance_budget.jsonl',run_id=out.name+'-acceptance',protocol_hash=p['protocol_hash'],**e.prior.config(0,1000,0))
 judge=e.prior.Judge(budget);rows=[];started=time.monotonic()
 for task,origin in zip(tasks,manifest['rows']):
  strict_stream_task(task);source=e.ROOT/origin['source']
  if e.sha(source)!=origin['source_sha256'] or fingerprint(task)!=origin['task_sha256']:raise ValueError('lineage hash changed')
  old=e.read(source)[origin['source_index']];reference=Path(old['reference_path'])
  if e.sha(reference)!=old['reference_sha256']:raise ValueError('reference hash changed')
  if len(old['public_cases'])!=len(task['public_cases']):raise ValueError('case count changed')
  parity=[]
  for i,(a,b) in enumerate(zip(old['public_cases'],task['public_cases'])):
   if (a['input'],a['expected'])!=(b['input'],b['expected']):raise ValueError('case changed')
   # Prior wrapper delegates exactly to OLD.accepts(inner); new trusted form
   # delegates to that same function. No replacement reference or generated oracle.
   expected=a['expected'];probes=[expected,expected.strip(),' \n'+expected+' \n',expected.swapcase(),'S19F_INVALID_FIXTURE','',expected+' 999999']
   outcomes=[dict(output=x,old=bool(e.prior.old.accepts(task['task_id'],a,x)),new=bool(e.prior.old.accepts(task['task_id'],b,x))) for x in probes]
   parity.append(dict(case_index=i,same=all(x['old']==x['new'] for x in outcomes),probes=outcomes,original_comparison=a.get('comparison'),frozen_comparison=b.get('comparison')))
  positive=judge.run(task['task_id'],reference.read_text(),task['public_cases'])
  invalid=judge.run(task['task_id'],"print('S19F_INVALID_FIXTURE')",task['public_cases'])
  runtime=judge.run(task['task_id'],"raise RuntimeError('S19F_INVALID_FIXTURE')",task['public_cases'])
  passed=positive['passed'] and not invalid['passed'] and not runtime['passed'] and all(x['same'] for x in parity)
  rows.append(dict(task_id=task['task_id'],reference_path=str(reference),reference_sha256=e.sha(reference),positive=positive,invalid=invalid,runtime=runtime,parity=parity,passed=passed,reason=None if passed else 'PUBLIC_REFERENCE_OR_REJECTION_OR_PARITY_FAILURE'))
  e.write(out/'scorer_acceptance.json',dict(real_api_calls=0,scope='previously exposed development public cases only; no final/hidden tests',completed=len(rows),expected=len(tasks),passed=len(rows)==len(tasks) and all(r['passed'] for r in rows),rows=rows,budget=budget.snapshot(),seconds=time.monotonic()-started))
  print(task['task_id'],passed,flush=True)
 selected=[t for t,r in zip(tasks,rows) if r['passed']]
 e.write(out/'tasks.json',selected);e.write(out/'task_manifest.json',dict(source=str(bundle/'tasks.json'),source_sha256=p['tasks_sha256'],selection='Frozen original order; remove only failed pre-model scorer acceptance; never substitute',original_count=len(tasks),count=len(selected),rows=[x for x,r in zip(manifest['rows'],rows) if r['passed']],excluded=[dict(task_id=r['task_id'],reason=r['reason']) for r in rows if not r['passed']],batches=[[t['task_id'] for t in selected[i:i+5]] for i in range(0,len(selected),5)],exposure='previously_exposed_development'))
 print('COMPLETE',len(selected),'of',len(tasks),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--bundle',required=True);a.add_argument('--output',required=True);v=a.parse_args();main(v.bundle,v.output)
