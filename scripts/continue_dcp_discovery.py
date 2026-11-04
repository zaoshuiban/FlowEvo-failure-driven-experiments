import json,time,collections
import run_dcp_discovery_verified as m
h=m.h;c=m.c;o=h.OUT
h.verify();p=h.load(o/'protocol.json');pr=h.load(o/'programs.json');out=h.load(o/'discovery.json')
h.save(o/'host_continuation.json',dict(reason='Missing json import in host differential wrapper after model response. No prompt, model source, budget or proposal changes; exact saved response replay, no resend.',source_sha256=h.sha(__file__),original_stop=h.load(o/'STOP.json')))
for kind,arm in p['order']:
 key=kind+'-'+arm
 if key in out:continue
 existing=list((o/'jobs').glob(kind+'-'+arm+'-discover-properties-*/reception.json'))
 if existing:
  assert len(existing)==1;receipt=h.load(existing[0])['receipt'];assert receipt['status']=='ACCEPTED';proposal=receipt['normalized']
 else:proposal=c.deliver(kind,arm,'discover','properties',h.public(kind,pr[kind]))
 receipt=h.assay(kind,pr[kind],proposal) if proposal else None;differential=None
 if arm=='P' and proposal:
  try:
   alt=json.loads(proposal['replacement_hypothesis']);a=c.make_artifact(kind,'P-hypothesis',alt,pr[kind]);comparisons=[];used=receipt['worker_input_count']
   if a['status']=='STATIC_VALID':
    for row in receipt['records']:
     for obs in row.get('observations',[]):
      if used>=16:break
      ex=c.execute(a,obs['parameters']);used+=1;comparisons.append(dict(parameters=obs['parameters'],alternative=ex,disagreement=ex.get('raw',{}).get('value')!=obs['actual'] if ex['status']=='EXECUTED_UNSCORED' and obs['actual'] is not None else None,original_status=obs['status'],alternative_status=h.classify(h.oracle(kind,obs['parameters']),ex)))
   differential=dict(artifact=a,comparisons=comparisons,total_worker_inputs=used)
  except (ValueError,KeyError,TypeError) as e:differential=dict(status='HYPOTHESIS_NOT_EXECUTABLE',reason=str(e))
 out[key]=dict(proposal=proposal,receipt=receipt,differential=differential);h.save(o/'discovery.json',out);print(key,collections.Counter(x['status'] for x in receipt['records']) if receipt else 'DELIVERY_FAILURE',flush=True)
h.save(o/'COMPLETE.json',dict(at=time.time(),repairs=0,host_replay=True))
