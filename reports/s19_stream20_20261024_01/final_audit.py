"""Offline audit, to run only after the real process has stopped."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import packet_check
from failure_evo.workflow_protocol_v2 import prepare,PreflightRejected
from failure_evo.contracts import fingerprint
PRE=Path(__file__).parent;RUN=ROOT/'runs/s19_stream20_20261024_01';plan=e.read(PRE/'plan.json')
changed=[f for f,h in plan['frozen_files'].items() if e.sha(ROOT/f)!=h]
assert not changed
requests=[]
for ch in ('solve','learning','validation'):
 audit=e.read(RUN/(ch+'_requests.json')) if (RUN/(ch+'_requests.json')).exists() else []
 for row in audit:
  if row['status']!='COMPLETED':continue
  matches=[p for p in (RUN/'wire'/ch).glob('*/request.json') if e.sha(p)==row['request_sha256'] and e.read(p.parent/'response.json')==row['raw_response']]
  assert len(matches)==1
  body=e.read(matches[0]);assert body['model']==plan['model'] and body['max_tokens']==8192 and body['thinking']=={'type':'disabled'}
  requests.append(dict(channel=ch,request_id=row['request_id'],request_sha256=row['request_sha256'],response_sha256=e.sha(matches[0].parent/'response.json'),model=body['model']))
preflight=[]
for path in sorted((RUN/'jobs').glob('*/*-messages.json')):
 messages=e.read(path);material=json.loads(messages[-1]['content']);packets=[packet_check(p) for p in material['source_packets']]
 record=dict(job_id=path.parent.name,slot=int(path.name.split('-')[0]),messages_sha256=e.sha(path),source_tasks=sorted({p['task_id'] for p in packets}),source_event_count=len(packets),source_packet_serialized_bytes=sum(len(json.dumps(p,ensure_ascii=False).encode()) for p in packets))
 try:
  prepared=prepare(messages,json_output=True);record.update(passed=True,input_upper=prepared.input_upper,request_sha256=prepared.sha256)
 except PreflightRejected as exc:
  record.update(passed=False,error=str(exc),details=vars(exc))
 preflight.append(record)
e.write(RUN/'final_audit.json',dict(frozen_files_unchanged=True,count=len(plan['frozen_files']),tasks_sha256=e.sha(PRE/'tasks.json'),wire_requests=requests,learning_preflight=preflight,real_additional_api_calls=0))
print(json.dumps(dict(frozen_files_unchanged=True,wire_requests=len(requests),learning_preflight=preflight),ensure_ascii=False,indent=2))
