import pathlib,sys,json,collections
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import s20_repair_stream as x
from failure_evo.workflow_protocol_v2 import memory_messages,prepare,Limits
from failure_evo.learning_contract import normalize
P=pathlib.Path(__file__).resolve().parent;M=R/'runs/s20_taco80_m_20261025_01';F=R/'runs/s20_taco80_f_20261025_01'
read=lambda p:json.loads(p.read_text());events=[json.loads(l) for l in (M/'stream.jsonl').read_text().splitlines()];used=set();results=[]
for event in events:
 if event['kind']!='MEMORY_STARTED':continue
 packets=[read(M/'public_packets'/(i+'.json')) for i in event['payload']['evidence_ids']];view=x.incremental_view(packets,used);messages=memory_messages('',view);r=prepare(messages,limits=Limits(),json_output=True);results.append(dict(included=len(view['included_ids']),omitted=len(view['omitted_ids']),input_upper=r.input_upper,wire_sha256=r.sha256));used.update(view['included_ids']);(P/f'memory_{len(results)}.json').write_text(json.dumps(dict(view=view,messages=messages),ensure_ascii=False,indent=2))
audit=[]
for f in F.glob('jobs/*/*-response.json'):
 response=read(f);check=normalize(response['text'],response['finish_reason']);mp=f.with_name(f.name.replace('response','messages'));messages=x.compile_messages(read(mp),{'compile_error':check.get('error')} if not check['accepted'] else None);r=prepare(messages,json_output=True);audit.append(dict(file=str(f.relative_to(R)),original_accepted=check['accepted'],error=check.get('error'),new_wire_upper=r.input_upper))
assert len(audit)==21 and len(results)==8
# Existing validators still reject wrong scalar types; no response coercion.
assert sum(a['original_accepted'] for a in audit)==2
(P/'replay.json').write_text(json.dumps(dict(model_requests=0,memory_batches=results,covered_events=len(used),compile_responses=audit,old_outcomes_unchanged=True),ensure_ascii=False,indent=2))
print('PASS',len(results),'M batches',len(used),'events;',len(audit),'F wires')
