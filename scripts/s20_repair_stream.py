"""Opt-in repair protocol; old stream, results and validators remain unchanged."""
import json,time,copy
import run_workflow_v2 as e
from run_learning_stream import LearningStream,restore_budget
from failure_evo import learning_evidence_bundle as leb
from failure_evo.contracts import canonical,fingerprint,strict_feedback
from failure_evo.repair_choice_v2 import STATES,ACTIONS,choose,generic_choice
VERSION='s20-repair-attribution-v1'
FIELDS=('conditions','action','expected_improvement','refusal_conditions','stop_conditions','unknowns')
RULE_SCHEMA={'type':'object','additionalProperties':False,'required':['hypothesis','rule'],'properties':{'hypothesis':{'type':'object','additionalProperties':False,'required':list(FIELDS),'properties':{k:{'type':'string','minLength':1} for k in FIELDS}},'rule':{'type':'object','additionalProperties':False,'required':['when','action','fallback'],'properties':{'when':{'type':'object','additionalProperties':False,'required':['candidate_state','public_result','remaining_calls_min'],'properties':{'candidate_state':{'type':'string','enum':list(STATES)},'public_result':{'type':'string','enum':['WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE']},'remaining_calls_min':{'type':'integer','minimum':1,'maximum':5}}},'action':{'type':'string','enum':list(ACTIONS)},'fallback':{'type':'string','enum':['NATIVE']}}}}}
DELIVERY='Return only one python fenced block containing a COMPLETE executable program. No prose, algorithm discussion, or long reasoning comments. Preserve correctness and input/output requirements; do not special-case examples. This is a delivery constraint, not permission to guess an algorithm.'
def incremental_view(packets,consumed):
 checked=[leb.check_packet(p) for p in packets];new=sorted((p for p in checked if p['event_id'] not in consumed),key=lambda p:(p['task_id'],p['stage'],p['event_id']))
 # Round robin across original tasks; never silently mark omitted events consumed.
 groups={}
 for p in new:groups.setdefault(p['task_id'],[]).append(p)
 ordered=[]
 while any(groups.values()):
  for k in sorted(groups):
   if groups[k]:ordered.append(groups[k].pop(0))
 selected=[]
 for p in ordered:
  row=dict(event_id=p['event_id'],task_id=p['task_id'],stage=p['stage'],artifact_state=p['artifact_state'],public_status=p['feedback']['status'],packet_sha256=fingerprint(p),packet_ref='public_packets/'+p['event_id']+'.json',code=leb.text_view(p['code'],400,'public_packets/'+p['event_id']+'.json/code'),public_feedback=[leb.case_view(c,'public_packets/'+p['event_id']+'.json/feedback') for c in p['feedback'].get('public_cases',[])[:1]])
  if len(canonical(selected+[row]).encode())>16000:break
  selected.append(row)
 return dict(version=VERSION,events=selected,included_ids=[x['event_id'] for x in selected],omitted_ids=[p['event_id'] for p in ordered if p['event_id'] not in {x['event_id'] for x in selected}],complete_input_manifest_sha256=fingerprint([(p['event_id'],fingerprint(p)) for p in new]))
def compile_messages(messages,diagnosis=None):
 out=copy.deepcopy(messages);out[0]['content']+='\nThe following is JSON Schema, NOT an example output. Enum arrays describe allowed scalar choices; NEVER copy arrays into scalar fields. Return exactly hypothesis and rule. '+canonical(RULE_SCHEMA)
 if diagnosis:out[0]['content']+='\nFix only the diagnosed contract error; it is NOT a failure of the source program. Do not turn compiler diagnostics into mechanism conditions. Diagnostic: '+canonical(diagnosis)
 return out
class RepairedStream(LearningStream):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw)
  if self.runner.plan.get('repair_protocol')!=VERSION:raise ValueError('explicit new frozen plan required')
 def learning_messages(self,job,prior,diagnosis):return compile_messages(super().learning_messages(job,prior,diagnosis),diagnosis)
 def boundary(self,completed):
  if self.arm!='M':return super().boundary(completed)
  records=self.log.records();used={i for r in records if r['kind']=='MEMORY_DELTA_COMMITTED' for i in r['payload']['included_ids']}
  view=incremental_view(list(self.packets.values()),used)
  if not view['included_ids']:return
  key=fingerprint([VERSION,self.runner.memory,view]);path=self.path/'memory_bundles'/(key+'.json');e.write(path,view)
  stream=self
  class Transport:
   def send(self,prepared,*,request_id,**kw):
    body=json.loads(prepared.wire);checked=e.prepare(body['messages'],limits=e.Limits(),json_output=True)
    assert checked.wire==prepared.wire
    return stream.send_prepared('learning',checked,request_id)
  result=e.update_memory(Transport(),self.runner.memory,view,request_prefix=key,allow_revision=True)
  self.runner.outputs[key]=result
  if result['updated']:
   self.runner.memory=result['memory'];self.runner.save();self.event('MEMORY_DELTA_COMMITTED',key=key,included_ids=view['included_ids'])
  else:self.runner.save();self.event('MEMORY_DELTA_REJECTED',key=key)
 def request(self,channel,request_id,messages,**kw):
  if channel=='validation':
   messages=copy.deepcopy(messages);messages[0]['content']+='\n'+DELIVERY
  return super().request(channel,request_id,messages,**kw)
 def assess(self,key,job,slot):
  rule=self.memory.state(key)['rule'];audit=[]
  for i in job['evidence_ids']:
   p=self.packets[i];f=strict_feedback(p['feedback']);b=restore_budget(p['checkpoint_budget']);action=choose(rule,p['code'],f,b);g=generic_choice(p['code'],f,b)
   audit.append(dict(event_id=i,action=action,generic_action=g,matched=action!='NATIVE',distinct=action!='NATIVE' and action!=g))
  e.write(self.path/'jobs'/job['job_id']/f'{slot}-pre-source-distinctness.json',dict(observations=audit,independent_decision_evidence=any(x['distinct'] for x in audit),request_identity='Common delivery instruction must also be used by future G/M controls; action equivalence alone does not prove native wire identity'))
  return super().assess(key,job,slot)
