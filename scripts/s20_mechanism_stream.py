"""Opt-in mechanism acceptance: durable M delta transaction, no new actions."""
import run_workflow_v2 as e
from s20_repair_stream import RepairedStream,incremental_view,VERSION
from failure_evo.contracts import fingerprint
import json
MECHANISM_VERSION='s20-mechanism-acceptance-v1'
class MechanismStream(RepairedStream):
 def boundary(self,completed):
  if self.arm!='M':return super().boundary(completed)
  rows=self.log.records();finished={r['payload']['key'] for r in rows if r['kind'] in ('MEMORY_DELTA_COMMITTED','MEMORY_DELTA_REJECTED')}
  started=next((r['payload'] for r in rows if r['kind']=='MEMORY_DELTA_STARTED' and r['payload']['key'] not in finished),None)
  if started is None:
   used={i for r in rows if r['kind']=='MEMORY_DELTA_COMMITTED' for i in r['payload']['included_ids']}
   view=incremental_view(list(self.packets.values()),used)
   if not view['included_ids']:return
   key=fingerprint([VERSION,self.runner.memory,view]);started=dict(key=key,previous_memory=self.runner.memory,view=view)
   # Freeze input before any send. Recovery never rebuilds it using newer memory.
   self.event('MEMORY_DELTA_STARTED',**started)
  key=started['key'];view=started['view'];stream=self
  e.write(self.path/'memory_bundles'/(key+'.json'),view)
  class Transport:
   def send(self,prepared,*,request_id,**kw):
    checked=e.prepare(json.loads(prepared.wire)['messages'],limits=e.Limits(),json_output=True)
    assert checked.wire==prepared.wire
    return stream.send_prepared('learning',checked,request_id)
  result=e.update_memory(Transport(),started['previous_memory'],view,request_prefix=key,allow_revision=True)
  self.fault('MEMORY_RESPONSE_PERSISTED')
  self.runner.outputs[key]=result
  if result['updated']:self.runner.memory=result['memory']
  self.runner.save();self.fault('MEMORY_STATE_SAVED')
  self.event('MEMORY_DELTA_COMMITTED' if result['updated'] else 'MEMORY_DELTA_REJECTED',key=key,included_ids=view['included_ids'] if result['updated'] else [])
