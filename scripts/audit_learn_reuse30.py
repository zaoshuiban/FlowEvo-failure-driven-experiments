"""Read-only post-run integrity checks; does not call providers or generated code."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
import learn_reuse30 as s
from failure_evo.evidence import EvidenceStore
from failure_evo.workflow_policy import WorkflowPolicy,WorkflowRegistry
from failure_evo.failure_events import FailureEvidenceStore

def main():
 p=s.verify();results=s.read(s.RUN/'results.json');assert results['status']=='COMPLETE';checks=[]
 def check(name,ok):
  checks.append(dict(name=name,passed=bool(ok)))
  if not ok:raise AssertionError(name)
 tasks=s.read(s.RUN/'tasks.json');old={x['task_id'] for x in s.read(s.SOURCE/'tasks.json')};check('30 distinct subsequent tasks',len(tasks)==len({x['task_id'] for x in tasks})==30);check('exclude all S13 tasks',not old & {x['task_id'] for x in tasks});check('90 unique branches',len(results['rows'])==len({(x['task_id'],x['arm']) for x in results['rows']})==90)
 check('all scorers accepted before API',s.read(s.RUN/'scoring_acceptance.json')['passed'])
 index={t['task_id']:t['index'] for t in tasks};allrequests=[]
 for path in s.RUN.rglob('requests.json'):
  for i,r in enumerate(s.read(path),1):
   raw=s.read(path.parent/f'response_{i}.json');u=raw['usage'];check(str(path.relative_to(s.RUN))+f':{i}:settled',r['status']=='COMPLETED' and u==r['usage']);check('request hash '+str(path)+str(i),r['request_sha256']==s.fingerprint(r['request']));check('serialized bytes '+str(path)+str(i),r['serialized_bytes']==len(s.canonical(r['request']).encode()));check('token bounds '+str(path)+str(i),u['prompt_tokens']<=r['input_token_upper'] and u['completion_tokens']<=8192);check('actual model '+str(path)+str(i),raw['model']==p['model']);allrequests.append(r)
 check('learning <=14',sum(r['capability']=='learn' for r in allrequests)<=14)
 reg=WorkflowRegistry(s.RUN/'registry.jsonl',FailureEvidenceStore(s.RUN/'evidence_F.jsonl'));cards={tuple(r['payload']['key']):WorkflowPolicy.from_dict(r['payload']['card']) for r in reg.events.records() if r['kind']=='SHADOW_REGISTERED'}
 for key,c in cards.items():
  review=reg.review(c);check(str(key)+' immutable artifact',c.intact());check(str(key)+' <=5 opportunities',review['opportunities_used']<=5);check(str(key)+' all opportunities completed',review['opportunities_used']==review['completed']);check(str(key)+' not active/mature',review['permission']!='active' and review['generation']!='mature')
 stop=s.read(s.RUN/'online_complete.json');check('registry unchanged by final audit',stop['registry_sha256']==(s.sha(s.RUN/'registry.jsonl') if (s.RUN/'registry.jsonl').exists() else None));check('learning unchanged by final audit',stop['learning_state_sha256']==s.sha(s.RUN/'learning_state.json'))
 for arm,h in stop['evidence_hashes'].items():check(arm+' evidence unchanged by audit',s.sha(s.RUN/f'evidence_{arm}.jsonl')==h)
 totalhooks=0
 for r in results['rows']:
  branch=s.RUN/'branches'/r['task_id']/r['arm'];w=s.read(branch/'workflow.json');req=s.read(branch/'requests.json');check(str(branch)+' bounded calls',len(req)<=5);check(str(branch)+' source lock',s.sha(branch/'final.py')==r['final_sha256']==s.read(branch/'final_lock.json')['sha256']);check(str(branch)+' audit starts after stream', (branch/'audit.json').stat().st_mtime>=stop['at']);check(str(branch)+' reported score',r['audit_pass']==s.read(branch/'audit.json')['passed'])
  for h in w['hook_events']:
   totalhooks+=1;c=cards[(h['operator_id'],h['version'])];auth=reg.state(c)['authorization'];check(str(branch)+' next batch authorization',auth['effective_from']<=index[r['task_id']] and auth['effective_from']%10==1);check(str(branch)+' at most one host call',h['actual_cost']['model_calls']<=1)
   if h['status']=='applied':check(str(branch)+' actual public verified proposal',h['public_check_outcome']=='passed' and h['verification']['status']=='PUBLIC_PASS' and r['final_sha256']==h['proposed_sha256'])
 check('hook/registry counts agree',totalhooks==sum(reg.state(c)['opportunities_used'] for c in cards.values()))
 for name in p['budgets']:
  b=s.make_budget(p,name);check(name+' no pending/unknown',not b.snapshot()['unknown_or_pending_requests']);check(name+' no exceeded money reserve',b.snapshot()['remaining_cost_microusd']>=0)
 # Historical results remain backed by their original frozen code, not edited retrospectively.
 original=s.read(s.SOURCE/'protocol.json')
 for f,h in original['frozen_files'].items():check('S13 preserved '+f,s.sha(f)==h)
 out=dict(passed=True,checks=len(checks),physical_requests=len(allrequests),actual_operator_invocations=totalhooks,details=checks);s.write(s.RUN/'integrity_audit.json',out);print(json.dumps({k:v for k,v in out.items() if k!='details'}))

if __name__=='__main__':main()
