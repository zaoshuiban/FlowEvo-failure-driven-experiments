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
P=R/'runs/s20_mechanism_acceptance_20261025_01';OLD=R/'runs/s20_taco80_f_20261025_01';M=R/'runs/s20_taco80_m_20261025_01';read=e.read
p=read(P/'plan.json');initial=p['f_jobs'];results=read(P/'progress.json');alltasks=read(R/'runs/s20_preparation_20261025_01/stream_tasks.json');task=next(t for t in alltasks if t['task_id']==p['continuation_task_id']);task={k:v for k,v in task.items() if k!='role'}
configure_worker(read(R/'reports/s19_v2_acceptance/worker_environment.json'));tempfile.tempdir=str(P/'tmp')
r=e.ExperimentRunner(P,p,sender_factory,resume=True);s=MechanismStream(r,[task],arm='M',batch_size=1)
assert r.budgets['solve'].calls==0 and not r.transports['solve'].audit,'No replay of a sent solve request'
used={i for x in s.log.records() if x['kind']=='MEMORY_DELTA_COMMITTED' for i in x['payload']['included_ids']};sources={s.packets[i]['task_id'] for i in used}
packets=[read(f) for f in (M/'public_packets').glob('*.json')];packet=min((x for x in packets if x['task_id'] not in sources),key=lambda x:(x['task_id'],x['stage'],x['event_id']))
e.write(P/'continuation_amendment.json',dict(reason='Original instrumentation patched prepare twice; no send occurred. Native M l1 never reads memory. Use frozen sorted historical public repair checkpoint, not an unseen outcome experiment.',source_packet=packet['event_id'],source_task=packet['task_id'],hard_budget_unchanged=True,new_calls_max=1))
try:
 from failure_evo.workflow_protocol_v2 import WorkflowClient
 client=WorkflowClient(r.transports['solve'],'M-use',memory=r.memory)
 payload=dict(task=packet['task_public'],stage='l2a',previous_candidate=packet['code'],feedback=packet['feedback'])
 messages=client.native_messages(payload);messages[0]['content']+='\n'+DELIVERY
 assert any(r.memory in m['content'] for m in messages)
 response=s.request('solve','M-use-public-checkpoint/1',messages,budget=restore_budget(packet['checkpoint_budget']))
 code=delivery(response['text'],response['finish_reason'])['code'];evaluation=r.judge.run(packet['task_id'],code,packet['public_cases'])
 e.write(P/'memory_use.json',dict(packet=packet,response=response,code=code,evaluation=evaluation,memory_sha256=fingerprint(r.memory),memory_in_actual_wire=any(r.memory in m['content'] for m in r.transports['solve'].audit[-1]['request']['messages']),causal_benefit_proven=False))
 count=r.budgets['learning'].calls;s.boundary(0);results['M']['resume_no_repeat']=count==r.budgets['learning'].calls;results['M']['injected']=True;results['M']['continuation_status']=evaluation['status'];e.write(P/'progress.json',results)
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
