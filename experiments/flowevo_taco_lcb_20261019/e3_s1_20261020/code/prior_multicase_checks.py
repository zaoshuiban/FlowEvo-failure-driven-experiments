"""Check cross-case state/cursor behavior for reused trusted single-case probes."""
import collections,json,sys
from replay import R,B,read,write,Worker
sys.path.insert(0,str(B/'trusted_rgf_20261020/code'))
from suite import accepts as prior_accepts
from contracts_audit import audit as prior_audit
def main():
 manifest=read(R/'review_manifest.json');suite=read(R/'public_suite.json')['cases'];rows=[];executions=0
 for t in manifest['tasks']:
  tid=t['task_id']
  if tid not in ['taco_0967','taco_0962','taco_0055','taco_0294','taco_0194']:continue
  cases=[x['prior_case'] for x in suite[tid][:2]]
  for c in cases:prior_audit(tid,c)
  inp='2\n'+''.join(c['input'].split('\n',1)[1] for c in cases)
  for a in t['historical_programs']:
   code=R/a['source_path'];status='NO_COMPLETE_CODE' if not code.read_text().strip() else None;actual=None
   if status is None:
    with Worker(code) as w:
     compiled=w.call({'mode':'compile_stdio','timeout':4})
     if compiled['status']!='OK':actual=compiled;status=compiled['status']
     else:
      actual=w.call({'mode':'stdio','input':inp,'timeout':4});executions+=1
      if actual['status']!='OK':status=actual['status']
      else:
       values=actual['output'].split();status='PASS' if len(values)==2 and all(prior_accepts(tid,c,v) for c,v in zip(cases,values)) else 'WRONG_ANSWER'
   rows.append({'task_id':tid,'stage':a['stage'],'code_sha256':a['code_sha256'],'status':status,'input':inp,'source_single_cases':cases,'actual':actual})
 write(R/'prior_multicase_results.json',{'tasks':5,'programs':len(rows),'executions':executions,'new_model_calls':0,'status_counts':dict(collections.Counter(x['status'] for x in rows)),'rows':rows})
 print('PRIOR MULTICASE',collections.Counter(x['status'] for x in rows),flush=True)
if __name__=='__main__':main()
