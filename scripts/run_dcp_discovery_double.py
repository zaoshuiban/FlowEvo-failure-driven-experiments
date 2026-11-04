import sys,time,collections,json
from pathlib import Path
import hard_math_dcp_double_base as h
c=h.core
h.OUT=h.ROOT/'runs/dcp_discovery_20261031_03';h.configure()
P='In replacement_hypothesis, provide a JSON-encoded object with code containing a complete alternative def solve(parameters). This is a candidate computational hypothesis, not a trusted oracle. Use the same sandbox restrictions as the supplied program: no I/O, eval, classes, annotations, nonlocal or top-level tests. Each test must use oracle_correct with right=null. The host will actually compare the original and alternative outputs. Propose at least two plausible competing computational hypotheses for the supplied program and task. Search actively for concrete inputs on which these hypotheses predict different outputs. State the competing hypotheses and predicted distinction in each claim; predictions are untrusted, never gold. No actual difference is itself proof of a bug. You may report no distinguishing input. '+c.STRUCT
c.DISCOVER_D=c.DISCOVER_D.replace('At most 8','At most 16')
c.DISCOVER_C=c.DISCOVER_C.replace('At most 8','At most 16')
P=P.replace('At most 8','At most 16')
original=c.Adapter.preflight
normalizer=c.Adapter._normalize_response
def normalize(self,raw):
 result=normalizer(self,raw)
 if self.arm=='P' and self.receipt and self.receipt['status']!='REJECTED':
  v=self.receipt['normalized']
  if any(t.get('relation')!='oracle_correct' or t.get('right') is not None for prop in v['properties'] for t in prop['tests']):raise ValueError('P_REQUIRES_SINGLE_INPUT_TESTS_TO_RESERVE_ALTERNATIVE_BUDGET')
 return result
c.Adapter._normalize_response=normalize
def preflight(self,r):
 if r['arm']!='P':return original(self,r)
 wire=original(self,dict(r,arm='C'));self.arm='P';wire['messages'][0]['content']=c.COMMON+P;return wire
c.Adapter.preflight=preflight

def main():
 h.freeze();o=h.OUT;p=h.load(o/'protocol.json');p.update(version='dcp-discovery-v1',order=[['score','D'],['score','C'],['score','P'],['digits','P'],['digits','C'],['digits','D'],['radical','D'],['radical','C'],['radical','P']],physical_max_calls=24,hard_budget_usd=4.8,repair_order=[],discovery_only=True,distinction='P alternative source is model-generated, statically checked and executed in identical Worker. Output disagreement and independent candidate error are separate. Total at most32 Worker input executions per arm.',repeats=1)
 p['source_hashes']['scripts/run_dcp_discovery_double.py']=h.sha(__file__);p['test_specs']=16;p['test_inputs_per_assay']=32;p['scope_note']='3 exposed original tasks, one sample per arm; not independent generalization';p['prompts']={'D':c.DISCOVER_D,'C':c.DISCOVER_C,'P':P}
 h.save(o/'protocol.json',p);h.save(o/'freeze.json',dict(sha256=h.fingerprint(p)));h.verify();h.preflight();h.save(o/'STARTED.json',dict(at=time.time()));pr=h.load(o/'programs.json');out={}
 try:
  for kind,arm in p['order']:
   proposal=c.deliver(kind,arm,'discover','properties',h.public(kind,pr[kind]));receipt=h.assay(kind,pr[kind],proposal) if proposal else None
   differential=None
   if arm=='P' and proposal:
    try:
     alt=json.loads(proposal['replacement_hypothesis']);a=c.make_artifact(kind,'P-hypothesis',alt,pr[kind]);comparisons=[];used=receipt['worker_input_count']
     if a['status']=='STATIC_VALID':
      for row in receipt['records']:
       for obs in row.get('observations',[]):
        if used>=32:break
        ex=c.execute(a,obs['parameters']);used+=1
        comparisons.append(dict(parameters=obs['parameters'],alternative=ex,disagreement=(ex.get('raw',{}).get('value')!=obs['actual']) if ex['status']=='EXECUTED_UNSCORED' and obs['actual'] is not None else None,original_status=obs['status'],alternative_status=h.classify(h.oracle(kind,obs['parameters']),ex)))
     differential=dict(artifact=a,comparisons=comparisons,total_worker_inputs=used)
    except (ValueError,KeyError,TypeError) as e:differential=dict(status='HYPOTHESIS_NOT_EXECUTABLE',reason=str(e))
   out[kind+'-'+arm]=dict(proposal=proposal,receipt=receipt,differential=differential);h.save(o/'discovery.json',out);print(kind,arm,collections.Counter(x['status'] for x in receipt['records']) if receipt else 'DELIVERY_FAILURE',flush=True)
  h.save(o/'COMPLETE.json',dict(at=time.time(),repairs=0))
 except BaseException as e:h.save(o/'STOP.json',dict(reason=str(e)));raise
if __name__=='__main__':main()
