import sys,time,collections
from pathlib import Path
import run_hard_math_property_probe as h
c=h.core
h.OUT=h.ROOT/'runs/dcp_discovery_20261031_01';h.SPECS={k:v for k,v in h.SPECS.items() if k in ('score','digits')};h.configure()
P='Propose at least two plausible competing computational hypotheses for the supplied program and task. Search actively for concrete inputs on which these hypotheses predict different outputs. State the competing hypotheses and predicted distinction in each claim; predictions are untrusted, never gold. No actual difference is itself proof of a bug. You may report no distinguishing input. '+c.STRUCT
original=c.Adapter.preflight
def preflight(self,r):
 if r['arm']!='P':return original(self,r)
 wire=original(self,dict(r,arm='C'));self.arm='P';wire['messages'][0]['content']=c.COMMON+P;return wire
c.Adapter.preflight=preflight

def main():
 h.freeze();o=h.OUT;p=h.load(o/'protocol.json');p.update(version='dcp-discovery-v1',order=[['score','D'],['score','C'],['score','P'],['digits','P'],['digits','C'],['digits','D']],physical_max_calls=12,hard_budget_usd=2.4,repair_order=[],discovery_only=True,distinction='Predicted differences are unverified model claims; host confirms candidate error independently. No claim that competing hypotheses were executed.',repeats=1)
 p['source_hashes']['scripts/run_dcp_discovery.py']=h.sha(__file__);p['prompts']={'D':c.DISCOVER_D,'C':c.DISCOVER_C,'P':P}
 h.save(o/'protocol.json',p);h.save(o/'freeze.json',dict(sha256=h.fingerprint(p)));h.verify();h.preflight();h.save(o/'STARTED.json',dict(at=time.time()));pr=h.load(o/'programs.json');out={}
 try:
  for kind,arm in p['order']:
   proposal=c.deliver(kind,arm,'discover','properties',h.public(kind,pr[kind]));receipt=h.assay(kind,pr[kind],proposal) if proposal else None;out[kind+'-'+arm]=dict(proposal=proposal,receipt=receipt);h.save(o/'discovery.json',out);print(kind,arm,collections.Counter(x['status'] for x in receipt['records']) if receipt else 'DELIVERY_FAILURE',flush=True)
  h.save(o/'COMPLETE.json',dict(at=time.time(),repairs=0))
 except BaseException as e:h.save(o/'STOP.json',dict(reason=str(e)));raise
if __name__=='__main__':main()
