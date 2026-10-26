import pathlib,sys,json,hashlib,itertools
from tokenizers import Tokenizer
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from failure_evo.workflow_protocol_v2 import WorkflowClient
from s20_repair_stream import DELIVERY
from run_learning_stream import restore_budget
O=pathlib.Path(__file__).parent;OLD=R/'runs/s20_gmp_pilot12_20261026_01';T=R.parent/'experiments/reasoning_token_attribution_and_replacement/tokenizer/tokenizer.json';tok=Tokenizer.from_file(str(T))
count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
m=e.read(OLD/'memory.json')['text'];p=(O/'generic_advice.txt').read_text();assert count(m)==count(p)==458
ids=[x['task_id'] for x in e.read(OLD/'screening.json') if x['decision']=='FIXED_LIMIT_REACHED'];assert len(ids)==6
assert not set(ids)&{x['task_id'] for x in e.read(OLD/'packets.json')}
stage={x:i for i,x in enumerate(['l1','l2a','l2b','l3','l4'])};pack=[]
for tid in ids:
 options=[]
 for arm in 'GMF':
  for f in (R/'runs'/f's20_taco80_{arm.lower()}_20261025_01/public_packets').glob('*.json'):
   q=e.read(f)
   if q['task_id']==tid and q['feedback']['status'] not in ('PUBLIC_PASS','UNKNOWN') and q['checkpoint_budget']['max_calls']>q['checkpoint_budget']['calls'] and q['checkpoint_budget']['remaining_seconds']>0:options.append((stage[q['stage']],str(f),q))
 pack.append(sorted(options,key=lambda x:x[:2])[0][2])
wires=[];failures=[]
for i,q in enumerate(pack):
 counts={}
 for arm in list(itertools.permutations('GMP'))[i]:
  c=WorkflowClient(None,'preflight',memory=m if arm=='M' else p if arm=='P' else '',library='');msg=c.native_messages(dict(task=q['task_public'],stage='l2a',previous_candidate=q['code'],feedback=q['feedback']));msg[0]['content']+='\n'+DELIVERY
  counts[arm]=sum(count(x['content']) for x in msg)
  try:
   w=e.prepare(msg);b=restore_budget(q['checkpoint_budget']);assert b.max_tokens-b.used_tokens>=w.input_upper+w.output_upper
  except Exception as exc:
   failures.append(dict(task_id=q['task_id'],arm=arm,error=str(exc)));continue
  wires.append(dict(index=i,task_id=q['task_id'],arm=arm,messages=msg,wire_sha256=w.sha256,input_upper=w.input_upper,output_upper=w.output_upper,local_content_tokens=counts[arm]))
 assert counts['M']==counts['P'];assert counts['M']-counts['G']==469
plan=dict(status='BLOCKED_INPUT_PREFLIGHT' if failures else 'PREPARED_ZERO_API_NOT_STARTED',preflight_failures=failures,proposed_run_id='s20_gmp_advice6_v2',tasks=ids,model='deepseek-flash',temperature=0,max_output_tokens=8192,max_calls=18,hard_usd_proposal=1.0,old_unknown_reservation_separate_usd=.018206,memory_source=str(OLD/'memory.json'),memory_raw_sha256=hashlib.sha256(m.encode()).hexdigest(),generic_raw_sha256=hashlib.sha256(p.encode()).hexdigest(),tokenizer_sha256=e.sha(T),matching='458 body tokens, +469 full message tokens for both M and P on all six checkpoints; server usage must confirm; no outcome-based padding',selection='six previously retained tasks in original order; no old-run unfinished tasks; development only',memory_updates=False,F_generation=False,confirmation_pool_access=False,continued_run=False,neutral_control='generic programming advice, not unrelated filler; same wrapper, no task-specific answers; written after prior reports, not claimed blind',decision='One bounded experiment only. Descriptive source-code audit of all discordances. Consider further study only if M has >=2 exclusive joint successes vs P and positive net joint successes vs G, with construction-inclusive cost per joint success <=1.25x G. Otherwise pause current fixed-memory design. Operational threshold, not power/significance proof. Infrastructure incomplete or token mismatch => inconclusive, no automatic retry or expansion.',stopping=['unknown request','Worker failure','data contamination','hard budget','frozen hash mismatch','provider M/P prompt-token mismatch'],scoring='historical public tests; original same-task held-out tests only after complete online lock, no independent-generalization claim',cost='cached/miss/output tokens separately; one historical memory build cost; pending reservations separate; local tool time separate',protocol_sources={str(f.relative_to(R)):e.sha(f) for f in [pathlib.Path(__file__),R/'scripts/run_workflow_v2.py',R/'scripts/s20_repair_stream.py',R/'FlowEvo/src/failure_evo/workflow_protocol_v2.py']})
for name,value in [('candidate_packets.json',pack),('frozen_wires.json',wires),('protocol.json',plan)]:e.write(O/name,value)
e.write(O/'freeze_hashes.json',{name:e.sha(O/name) for name in ['generic_advice.txt','candidate_packets.json','frozen_wires.json','protocol.json','tokenizer_calibration.json']});print(dict(candidate_tasks=6,ready_wires=len(wires),failures=failures,token_matching='PASS all six',new_api_calls=0))
