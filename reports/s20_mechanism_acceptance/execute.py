import pathlib,sys,json,time,copy,tempfile,requests
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from s20_mechanism_stream import MechanismStream,MECHANISM_VERSION
from s20_repair_stream import VERSION,DELIVERY,compile_messages,incremental_view
from run_learning_stream import restore_budget,configure_worker
from failure_evo.contracts import fingerprint,strict_feedback,PublicTaskView,strict_stream_task
from failure_evo.learning_contract import normalize
from failure_evo.repair_choice_v2 import choose,generic_choice,action_messages
from failure_evo.workflow_protocol_v2 import delivery
from experiment_s16b2_source import sender_factory
P=R/'runs/s20_mechanism_acceptance_20261025_01';OLD=R/'runs/s20_taco80_f_20261025_01';M=R/'runs/s20_taco80_m_20261025_01';assert not P.exists(),'no automatic paid replay'
read=e.read
# Selection frozen from request order, not observed source success or candidate quality.
initial=[a['request_id'].split('/')[0] for a in read(OLD/'learning_requests.json') if a['request_id'].endswith('/generate/0')][:2]
oldviews=[read(R/f'reports/s20_repair_attribution/memory_{i}.json')['view'] for i in range(1,9)]
consumed={i for v in oldviews for i in v['included_ids']};allids={p.stem for p in (M/'public_packets').glob('*.json')};tail=sorted(allids-consumed);assert len(tail)==4
first=oldviews[0]['included_ids'];alltasks=read(R/'runs/s20_preparation_20261025_01/stream_tasks.json');source_tasks={read(M/'public_packets'/(i+'.json'))['task_id'] for i in first+tail};task=next(t for t in alltasks if t['task_id'] not in source_tasks);task={k:v for k,v in task.items() if k!='role'};strict_stream_task(task)
quote=requests.get('https://api-docs.deepseek.com/quick_start/pricing/',timeout=20);quote.raise_for_status();assert all(v in quote.text for v in ('$0.3','$1.2'))
budgets={}
for ch,n,tools,cost in [('learning',8,0,500000),('solve',1,100,100000),('validation',4,400,300000)]:
 cfg=e.prior.config(n,tools,n*40960);cfg['max_cost_microusd']=cost;budgets[ch]=cfg
files=[R/'scripts/s20_mechanism_stream.py',R/'scripts/s20_repair_stream.py',pathlib.Path(__file__)];files+=list((R/'FlowEvo/src/failure_evo').glob('*.py'))
p=dict(run_id=P.name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='real_experiment',operator_representation='repair-choice-json-v2',repair_protocol=VERSION,mechanism_protocol=MECHANISM_VERSION,frozen_files={str(f.relative_to(R)):e.sha(f) for f in files},budgets=budgets,per_task=dict(max_calls=1,max_tokens=40960,max_tools=100,wall_seconds=600),allow_bounded_trials=False,rule_hook_enabled=False,first_memory_ids=first,tail_memory_ids=tail,continuation_task_id=task['task_id'],f_jobs=initial,selection='first two historical initial jobs in send order; no result-based replacement',source_policy='only matched distinct action evaluated, paired Generic one request each, same DELIVERY and max output; earliest legal public source',stage3='only after M persisted and injected and F distinct source effectiveness established; no automatic long stream',hard_usd=.9)
p['protocol_hash']=fingerprint(p);configure_worker(read(R/'reports/s19_v2_acceptance/worker_environment.json'))
# Common delivery requirement for ALL solve and source arms, never F-only.
def factory(ch):
 base=sender_factory(ch)
 def send(wire):return base(wire)
 return send
r=e.ExperimentRunner(P,p,factory);(P/'pricing.html').write_text(quote.text);(P/'tmp').mkdir();tempfile.tempdir=str(P/'tmp')
e.write(P/'authorization.json',dict(scope='bounded real M/F mechanism acceptance',user_basis='prior small API authorization plus current request',hard_usd=.9,max_requests=13,old_balance_inherited=False))
results=dict(M={},F=[])
def stream():return MechanismStream(r,[task],arm='M',batch_size=1)
s=stream()
try:
 for label,ids in [('first',first),('tail',tail)]:
  for i in ids:
   packet=read(M/'public_packets'/(i+'.json'));e.write(P/'public_packets'/(i+'.json'),packet);s.packets[i]=packet
  s.boundary(0);results['M'][label]=dict(memory_nonempty=bool(r.memory),memory_sha256=fingerprint(r.memory),committed_ids=[i for x in s.log.records() if x['kind']=='MEMORY_DELTA_COMMITTED' for i in x['payload']['included_ids']]);e.write(P/'progress.json',results)
 # Actual restart and boundary replay must not create a request after successful commit.
 count=r.budgets['learning'].calls;r.save();r=e.ExperimentRunner(P,p,factory,resume=True);s=stream();s.boundary(0);results['M']['resume_no_repeat']=r.budgets['learning'].calls==count
 if r.memory:
  from failure_evo.repair_choice import RepairChoiceClient
  # Native controller builds actual M request including memory; inject common system instruction before prepare.
  original=e.prepare
  # Native WorkflowClient uses module prepare, not this alias.
  import failure_evo.workflow_protocol_v2 as wp
  prior_prepare=wp.prepare
  def shared_prepare(messages,**kw):
   messages=copy.deepcopy(messages);messages[0]['content']+='\n'+DELIVERY;return prior_prepare(messages,**kw)
  wp.prepare=shared_prepare
  result=r.solve('M',task);wp.prepare=prior_prepare
  audit=r.transports['solve'].audit[-1];wire=audit['request'];results['M']['injected']=r.memory in json.dumps(wire,ensure_ascii=False);results['M']['continuation_status']=result['status'];results['M']['continuation_calls']=r.budgets['solve'].calls
 for jid in initial:
  base=read(OLD/'jobs'/jid/'0-messages.json');bundle=read(OLD/'jobs'/jid/'0-evidence-bundle.json')['bundle'];history=[];diag=None
  for slot in range(2):
   messages=compile_messages(base,diag);response=s.request('learning',f'F/{jid}/{slot}',messages,json_output=True);a=normalize(response['text'],response['finish_reason']);e.write(P/'F'/jid/f'{slot}.json',dict(response=response,normalization=a));history.append(dict(slot=slot,accepted=a['accepted'],error=a.get('error')))
   if a['accepted']:break
   diag=dict(compile_error=a['error'])
  record=dict(job_id=jid,attempts=history)
  if a['accepted']:
   rule=a['normalized']['rule'];record['rule']=rule;record['rule_sha256']=fingerprint(rule);obs=[]
   for event in bundle['events']:
    packet=read(OLD/event['packet_ref']);b=restore_budget(packet['checkpoint_budget']);f=strict_feedback(packet['feedback']);act=choose(rule,packet['code'],f,b);g=generic_choice(packet['code'],f,b);obs.append(dict(event_id=packet['event_id'],task_id=packet['task_id'],action=act,generic_action=g,matched=act!='NATIVE',distinct=act!='NATIVE' and act!=g,observed_at=event['observed_at']))
   record['observations']=obs;record['permission']='shadow';e.write(P/'F'/jid/'pre_source_audit.json',record)
   distinct=[o for o in obs if o['distinct']]
   if distinct:
    o=min(distinct,key=lambda o:(o['observed_at'],o['event_id']));packet=read(OLD/'public_packets'/(o['event_id']+'.json'));checks=s.safety(rule,packet);record['safety']=checks
    if all(checks.values()):
     record['paired_source']={}
     for arm,action in [('G',o['generic_action']),('F',o['action'])]:
      messages=action_messages(action,PublicTaskView.project(packet['task_public']),packet['code'],strict_feedback(packet['feedback']));messages[0]['content']+='\n'+DELIVERY
      response=s.request('validation',f'{jid}/source/{arm}',messages,budget=restore_budget(packet['checkpoint_budget']));code=delivery(response['text'],response['finish_reason'])['code'];evaluation=e.prior.Judge(r.budgets['validation']).run(packet['task_id'],code,packet['public_cases']);record['paired_source'][arm]=dict(response=response,evaluation=evaluation,code=code)
   else:record['decision']='NO_DISTINCT_ACTION_VALUE; no paid source retry'
  results['F'].append(record);e.write(P/'progress.json',results)
 e.write(P/'result.json',results);print('MECHANISM_ACCEPTANCE_COMPLETE',flush=True)
finally:r.save()
