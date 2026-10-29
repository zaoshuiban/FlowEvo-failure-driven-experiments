"""Report real GPT attempts, incomplete/unknown and zero-API work separately."""
import json,hashlib,collections,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import fingerprint
from failure_evo.persistent_budget import PersistentBudget

def main(run,out):
 out.mkdir(parents=True,exist_ok=True)
 def save(name,v):(out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 costs=[];budgets={};mechanisms=[];unknown=[];keys=[];statuses={}
 for d in sorted(p for p in run.iterdir() if p.is_dir() and (p/'provider.jsonl').exists()):
  records=[json.loads(x) for x in (d/'provider.jsonl').read_text().splitlines()]
  for r in records:
   if r['kind']=='SEND_STARTED':keys.append((d.name,r['payload']['key']))
   if r['kind']=='SEND_UNKNOWN':unknown.append(dict(job=d.name,**r['payload']))
   if r['kind']=='RAW_RESPONSE':
    raw=r['payload']['response'];u=raw['usage'];costs.append(dict(job=d.name,response_id=raw['id'],request_key=r['payload']['key'],finish_reason=raw['choices'][0]['finish_reason'],input_tokens=u['prompt_tokens'],output_tokens=u['completion_tokens'],reasoning_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens',0),total_tokens=u['total_tokens'],provider_reported_cost=u.get('cost'),response_sha256=r['payload']['sha256']))
  cfg=json.loads((d/'budget.jsonl').read_text().splitlines()[0])['payload']['config'];cfg.pop('cost_unit');cfg.pop('currency');budgets[d.name]=PersistentBudget(d/'budget.jsonl',**cfg).snapshot()
  if (d/'mechanism.json').exists():mechanisms.append(dict(job=d.name,**json.loads((d/'mechanism.json').read_text())))
  if (d/'result.json').exists():statuses[d.name]=json.loads((d/'result.json').read_text())
  else:statuses[d.name]=dict(status='UNKNOWN_SOURCE_REQUEST' if d.name=='T3' else json.loads((d/'mechanism.json').read_text())['normalized']['generation_decision'])
 workers=[]
 for p in (out/'mock_acceptance_final').glob('*/worker.jsonl'):
  workers.extend(json.loads(x)['payload'] for x in p.read_text().splitlines())
 historical=json.loads((run/'history_integrity.json').read_text());assert all(historical.values());assert len(keys)==len(set(keys))
 summary=dict(status='PARTIAL_ENGINEERING_IMPLEMENTED_REAL_SOURCE_NOT_DELIVERED',actual_requests=len(keys),responses=len(costs),unknown=len(unknown),mechanisms=len(mechanisms),decisions=dict(collections.Counter(m['normalized']['generation_decision'] for m in mechanisms)),
  input_tokens=sum(x['input_tokens'] for x in costs),output_tokens=sum(x['output_tokens'] for x in costs),reasoning_tokens=sum(x['reasoning_tokens'] for x in costs),total_tokens=sum(x['total_tokens'] for x in costs),provider_reported_cost=sum(x['provider_reported_cost'] for x in costs),
  reserved_upper_bound_usd=sum(b['charged_or_reserved_cost_microusd'] for b in budgets.values())/1000000,
  real_source_versions=0,real_test_proposals=0,development_comparisons=0,gate_executions=0,experimental=0,
  mock_tests=15,mock_real_worker_calls=len(workers),mock_worker_seconds=sum(x['seconds'] for x in workers),old_math_runs_unchanged=True,stopped_for='HTTP 402 Payment Required; UNKNOWN retained, no resend',component_followup='IMPLEMENTED_AND_PREFLIGHTED_NOT_EXECUTED')
 save('summary.json',summary);save('real_request_costs.json',costs);save('budgets.json',budgets);save('mechanisms.json',mechanisms);save('unknown_requests.json',unknown);save('branch_statuses.json',statuses)
 save('version_matrix.json',[dict(operator=i,V0='P2_FROZEN',V1='NOT_GENERATED',V2='NOT_GENERATED',V3='NOT_GENERATED',reason='No complete GPT split source; do not invent ablations') for i in (1,2,3)])
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
