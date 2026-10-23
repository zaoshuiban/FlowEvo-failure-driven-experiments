"""Zero-API integrity and descriptive failure audit; never changes the frozen run."""
import json, hashlib, collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'runs/s13_compare30_20261022_01'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
p=read(R/'protocol.json');d=read(R/'results.json');rows=d['rows'];checks=[]
for f,h in p['frozen_files'].items():checks.append(dict(check='frozen_file',path=f,passed=sha(Path(f))==h))
prev='0'*64;settled={};requests={}
for raw in (R/'budget.jsonl').read_text().splitlines():
 x=json.loads(raw);h=x.pop('record_hash');assert x['previous_hash']==prev;assert hashlib.sha256(canonical(x).encode()).hexdigest()==h;prev=h
 if x['kind']=='RESERVED':requests[x['payload']['request_id']]=x['payload']
 if x['kind']=='SETTLED':settled[x['payload']['request_id']]=x['payload']
counts={};first=[];failure=[];unknown=[]
for arm in p['arms']:
 c=collections.Counter()
 for r in [r for r in rows if r['arm']==arm]:
  path=R/'branches'/r['task_id']/arm;req=read(path/'requests.json');workflow=read(path/'workflow.json');lock=read(path/'final_lock.json');audit=read(path/'audit.json')
  checks.append(dict(check='final_lock',task=r['task_id'],arm=arm,passed=sha(path/'final.py')==lock['sha256']==r['final_sha256']))
  checks.append(dict(check='score_aggregation',task=r['task_id'],arm=arm,passed=audit['passed']==r['audit_pass'] and len(req)==r['model_calls']))
  lengths=0
  for i,q in enumerate(req,1):
   rid=str(path.relative_to(R))+f'/request_{i}';body=q['request'];reserved=requests[rid]
   assert reserved['request_hash']==hashlib.sha256(canonical(body).encode()).hexdigest()
   assert reserved['input_upper']==q['input_token_upper']
   responsepath=path/f'response_{i}.json'
   if not responsepath.exists() or q.get('status')!='COMPLETED':unknown.append(rid);continue
   raw=read(responsepath);assert raw['usage']['total_tokens']==settled[rid]['tokens'];lengths+=raw['choices'][0].get('finish_reason')=='length'
  c['truncated_responses']+=lengths;c['branches_with_truncation']+=bool(lengths);c['recovered_despite_truncation']+=bool(lengths and r['audit_pass'])
  if not r['audit_pass']:
   category='no_final_program' if not (path/'final.py').read_text().strip() else 'offline_wrong_answer' if audit['status']=='WRONG_ANSWER' else audit['status']
   c[category]+=1;failure.append(dict(task_id=r['task_id'],arm=arm,category=category,workflow_status=r['status'],workflow_error=workflow.get('error'),truncated_responses=lengths,public_statuses=[x.get('public_feedback',{}).get('status') for x in workflow.get('events',[]) if 'stage' in x],runtime_errors=[x.get('error') for x in workflow.get('events',[]) if 'error' in x]))
 counts[arm]=dict(c)
for t in read(R/'tasks.json'):
 a=R/'branches'/t['task_id']/'FlowEvo/requests.json';b=R/'branches'/t['task_id']/'FailureLearning/requests.json'
 if a.exists() and b.exists():
  aa,bb=read(a),read(b)
  if aa and bb:first.append(dict(task_id=t['task_id'],identical=aa[0]['request']==bb[0]['request']))
result=dict(status='PASS' if all(x['passed'] for x in checks) and all(x['identical'] for x in first) else 'FAIL',completed_branches=len(rows),checks=len(checks),failed_checks=[x for x in checks if not x['passed']],budget_chain_records=sum(1 for _ in (R/'budget.jsonl').read_text().splitlines()),first_requests=first,failure_categories=counts,failure_details=failure,unknown_requests=unknown)
(R/'integrity_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['first_requests','failure_details']},ensure_ascii=False,indent=2))
