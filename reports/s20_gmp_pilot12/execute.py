"""Preselected development checkpoint pairs; immutable memory; no learning or F generation."""
import pathlib,sys,json,time,tempfile,requests,hashlib
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker,restore_budget
from itertools import permutations
from failure_evo.contracts import fingerprint
from failure_evo.workflow_protocol_v2 import WorkflowClient,delivery
from experiment_s16b2_source import sender_factory
from s20_repair_stream import DELIVERY
P=R/'runs/s20_gmp_pilot12_20261026_01';assert not P.exists(),'new run only, no paid automatic replay'
SRC=R/'runs/s20_mechanism_acceptance_20261025_01';OLD=R/'runs/s20_taco80_m_20261025_01';B=R/'runs/s20_preparation_20261025_01'
prior=e.read(SRC/'plan.json');excluded={e.read(SRC/'public_packets'/(i+'.json'))['task_id'] for i in prior['first_memory_ids']+prior['tail_memory_ids']};excluded.add(e.read(SRC/'memory_use.json')['packet']['task_id']);excluded.add('s19g_taco-train-s00-r2749');excluded.update(x['task_id'] for x in e.read(R/'runs/s20_m_paired12_20261025_01/packets.json'));memory=e.read(SRC/'state.json')['memory']
tasks=e.read(B/'stream_tasks.json');order={t['task_id']:i for i,t in enumerate(tasks)};stage={k:i for i,k in enumerate(['l1','l2a','l2b','l3','l4'])};packets=[]
for arm in 'GMF':
 for f in (R/'runs'/f's20_taco80_{arm.lower()}_20261025_01'/'public_packets').glob('*.json'):
  q=e.read(f);q['_origin']=str(f.relative_to(R));packets.append(q)
selected=[];screen=[]
for tid in sorted({p['task_id'] for p in packets},key=lambda t:order[t]):
 if tid in excluded:screen.append(dict(task_id=tid,decision='EXCLUDED_MEMORY_OR_PRIOR_USE'));continue
 options=sorted((p for p in packets if p['task_id']==tid),key=lambda p:(stage[p['stage']],p['_origin']))
 legal=[p for p in options if p['feedback']['status'] not in ('PUBLIC_PASS','UNKNOWN') and p['checkpoint_budget']['max_calls']>p['checkpoint_budget']['calls'] and p['checkpoint_budget']['remaining_seconds']>0]
 if not legal:screen.append(dict(task_id=tid,decision='NO_REMAINING_CALL'));continue
 if len(selected)>=12:screen.append(dict(task_id=tid,decision='FIXED_LIMIT_REACHED'));continue
 selected.append({k:v for k,v in legal[0].items() if k!='_origin'});screen.append(dict(task_id=tid,event_id=legal[0]['event_id'],decision='SELECTED'))
assert len(selected)==12,'insufficient eligible tasks; no replacement search'
quote=requests.get('https://api-docs.deepseek.com/quick_start/pricing/',timeout=20);quote.raise_for_status();assert all(v in quote.text for v in ('$0.3','$1.2'))
# Preflight every exact wire before any paid request; one native repair per branch.
neutral_seed=('The small gallery has a pale green door. A wooden shelf stands beside a window. On the shelf are a ceramic bowl, a folded linen cloth, and a glass vase. A visitor walks through the courtyard and notices the gentle shade of the trees. The rooms are quiet during the afternoon. A painted landscape hangs above a plain bench. The soft colors in the picture resemble a distant garden. ' )
neutral=(neutral_seed*((len(memory)//len(neutral_seed))+1))[:len(memory)]
assert len(neutral)==len(memory)
wires=[]
for i,packet in enumerate(selected):
 arms=list(permutations('GMP'))[i%6]
 for arm in arms:
  client=WorkflowClient(None,'preflight',memory=memory if arm=='M' else neutral if arm=='P' else '',library='')
  payload=dict(task=packet['task_public'],stage='l2a',previous_candidate=packet['code'],feedback=packet['feedback'])
  messages=client.native_messages(payload);messages[0]['content']+='\n'+DELIVERY
  prepared=e.prepare(messages);budget=restore_budget(packet['checkpoint_budget']);assert budget.max_tokens-budget.used_tokens>=prepared.input_upper+prepared.output_upper
  wires.append(dict(index=i,arm=arm,task_id=packet['task_id'],messages=messages,wire_sha256=prepared.sha256,input_upper=prepared.input_upper,output_upper=prepared.output_upper))
# Assert the actual prompt difference is exactly the frozen memory advice block.
for i in range(12):
 pair={w['arm']:w for w in wires if w['index']==i};g=pair['G']['messages'];m=pair['M']['messages'];assert g[0]==m[0];assert m[1]['content']==g[1]['content']+'\nPreviously learned failure experience (advice, not proof):\n'+memory
 assert pair['P']['messages'][0]==g[0] and pair['P']['messages'][1]['content']==g[1]['content']+'\nPreviously learned failure experience (advice, not proof):\n'+neutral
cfg=e.prior.config(36,1600,36*40960);cfg['max_cost_microusd']=2000000
p=dict(run_id=P.name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='real_experiment',frozen_files={str(f.relative_to(R)):e.sha(f) for f in [pathlib.Path(__file__),R/'scripts/s20_repair_stream.py',R/'scripts/run_workflow_v2.py',R/'FlowEvo/src/failure_evo/workflow_protocol_v2.py']},budgets={'solve':cfg},memory_sha256=fingerprint(memory),source_memory=str(SRC.relative_to(R)),excluded_tasks=sorted(excluded),selection='Union G/M/F historical public failures; original frozen task order; earliest stage then origin path tie-break; exclude memory sources, prior paired12,612,2749; first12 without outcome selection',pairs=[dict(task_id=x['task_id'],event_id=x['event_id'],packet_sha256=fingerprint(x)) for x in selected],request_hashes=[w['wire_sha256'] for w in wires],maximum_model_requests=36,per_branch_calls=1,hard_usd=2.0,confirmation_pool_used=False,neutral_control=dict(character_count=len(neutral),text_sha256=fingerprint(neutral),matching='unicode character count only; actual provider token deltas reported, no exact tokenizer claim',wrapper='same failed-experience label as M to hold framing constant; semantically unrelated gallery text; not assumed inert'),decision_point='No automatic further runs. Positive exploratory direction requires at least 3 M-only joint successes vs G, positive net successes vs P, and full estimated cost per joint success <=1.25x G; thresholds operational, not statistical proof. If not met pause current fixed-memory approach rather than extend until significant.',library='empty identically; no arm-specific success experience confound',final_review='same frozen historical tests only after all branches locked; development evidence not unseen generalization')
p['protocol_hash']=fingerprint(p);configure_worker(e.read(B/'plan_G.json')['worker_environment']);r=e.ExperimentRunner(P,p,sender_factory);(P/'tmp').mkdir();tempfile.tempdir=str(P/'tmp');(P/'pricing.html').write_text(quote.text)
e.write(P/'authorization.json',dict(user_basis='Prior small API permission and current paired-mechanism experiment request',hard_usd=2.0,max_requests=36,no_budget_inheritance=True));e.write(P/'screening.json',screen);e.write(P/'packets.json',selected);e.write(P/'frozen_wires.json',wires);e.write(P/'memory.json',dict(text=memory,sha256=fingerprint(memory)));e.write(P/'neutral.json',dict(text=neutral,sha256=fingerprint(neutral)));out=[]
try:
 for w in wires:
  packet=selected[w['index']];prepared=e.prepare(w['messages']);assert prepared.sha256==w['wire_sha256'];response=r.transports['solve'].send(prepared,request_id=f"{w['arm']}/{w['task_id']}/repair1",capability='G-M-P-paired-native-repair',task_budget=restore_budget(packet['checkpoint_budget']))
  code=delivery(response['text'],response['finish_reason'])['code'];result=r.judge.run(packet['task_id'],code,packet['public_cases']);out.append(dict(index=w['index'],arm=w['arm'],task_id=packet['task_id'],response=response,code=code,code_sha256=hashlib.sha256(code.encode()).hexdigest(),public_result=result,request_sha256=prepared.sha256));e.write(P/'branches.json',out);r.save();print('PAIR',w['index']+1,w['arm'],result['tests_passed'],result['tests_run'],flush=True)
 e.write(P/'online_lock.json',dict(locked=True,branches=len(out),at=time.time(),branches_sha256=e.sha(P/'branches.json')))
finally:r.save()
