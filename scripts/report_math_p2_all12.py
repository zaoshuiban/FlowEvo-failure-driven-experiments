"""Read-only P2 receipts; no gold loading or correctness scoring."""
import json,hashlib,collections,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import fingerprint,canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.math_p2_all_failures import AllFailuresGPTAdapter
from failure_evo.persistent_budget import PersistentBudget

def main(root,out):
 out.mkdir(parents=True,exist_ok=True)
 def save(name,v):(out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 p=json.loads((root/'protocol.json').read_text());provider=EvidenceStore(root/'provider.jsonl').records();comp=EvidenceStore(root/'compiler.jsonl').records()
 sends=[x['payload'] for x in provider if x['kind']=='SEND_STARTED'];raws=[x['payload'] for x in provider if x['kind']=='RAW_RESPONSE'];costs=[]
 for raw in raws:
  a=raw['response'];u=a['usage'];cache=u.get('prompt_tokens_details',{}).get('cached_tokens',0);ipt=u['prompt_tokens'];opt=u['completion_tokens']
  costs.append(dict(request_key=raw['key'],response_id=a['id'],model=a['model'],finish_reason=a['choices'][0]['finish_reason'],input_tokens=ipt,output_tokens=opt,total_tokens=u['total_tokens'],reasoning_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens',0),cached_input_tokens=cache,
   quote_uncached_usd=(ipt*2.5+opt*15)/1000000,quote_cache_adjusted_usd=((ipt-cache)*2.5+cache*.25+opt*15)/1000000,provider_reported_cost_usd=u.get('cost'),raw_response_sha256=raw['sha256']))
 journal=root/'candidates_bound/engineering.jsonl';er=EvidenceStore(journal).records();reviews=[r['payload'] for r in er if r['kind']=='CANDIDATE_ENGINEERING']
 # Verify actual executed source is the exact raw GPT code, not a host algorithm.
 raw_codes={json.loads(x['response']['choices'][0]['message']['content']).get('code') for x in raws}
 artifacts=[]
 for r in reviews:
  a=r['artifact'];code=Path(a['source_path']).read_text();assert code in raw_codes and hashlib.sha256(code.encode()).hexdigest()==a['code_sha256']
  assert all(c['result']['code_sha256']==a['code_sha256'] and c['result']['gold_exposed'] is False for c in r['calls'])
  artifacts.append(dict(slot=r['slot'],version=a['version'],code_sha256=a['code_sha256'],source_path=a['source_path'],source_event_ids=a['source_event_ids'],static=r['static'],engineering_passed=r['engineering_passed'],calls=r['calls'],mathematical_correctness='NOT_EVALUATED',permission='SHADOW_ONLY'))
 old=json.loads((root/'historical_integrity.json').read_text());assert all(old.values())
 freeze=json.loads((root/'freeze.json').read_text());assert fingerprint(p)==freeze['protocol_sha256']
 assert all(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==d for rel,d in p['source_hashes'].items())
 assert len(sends)==len({r['key'] for r in sends})
 assert all(fingerprint(r['wire'])==r['wire_sha256'] for r in sends)
 for r in sends:
  payload=json.loads(r['wire']['messages'][1]['content']);assert len(payload['evidence']['events'])==12
  for event in payload['evidence']['events']:
   assert event['correct'] is False and set(event)=={'evidence_id','task_id','problem','correct','wrong_answer','attempts','sequence','episode_id','locked_sha256','lineage'}
  if 'engineering_diagnostics' in payload:assert set(payload['engineering_diagnostics'])=={'static_errors','execution_statuses'}
  assert 'gold_answer' not in canonical(payload) and 'scorer' not in canonical(payload)
 completion=json.loads((root/'COMPLETE.json').read_text()) if (root/'COMPLETE.json').exists() else json.loads((root/'RECOVERY_STOP.json').read_text())
 summary=dict(run_id=root.name,status='ENGINEERING_COMPLETE_WITH_PROVENANCE_AMENDMENT' if (root/'COMPLETE.json').exists() else 'PARTIAL',source_failures=12,
  mechanisms=3,source_versions=len(reviews),engineering_passed=sum(x['engineering_passed'] for x in reviews),real_gpt_responses=len(raws),new_deepseek_calls=0,
  source_execution_count=sum(c['role']=='source-execution-only' for r in reviews for c in r['calls']),refusal_controls=sum(c['role']=='nonmathematical-refusal' for r in reviews for c in r['calls']),
  execution_status_counts=dict(collections.Counter(c['result']['status'] for r in reviews for c in r['calls'])),
  worker_wall_seconds=sum(c['result']['seconds'] for r in reviews for c in r['calls']),
  input_tokens=sum(x['input_tokens'] for x in costs),output_tokens=sum(x['output_tokens'] for x in costs),total_tokens=sum(x['total_tokens'] for x in costs),reasoning_tokens=sum(x['reasoning_tokens'] for x in costs),
  estimated_uncached_usd=sum(x['quote_uncached_usd'] for x in costs),estimated_cache_adjusted_usd=sum(x['quote_cache_adjusted_usd'] for x in costs),provider_reported_cost_usd=sum(x['provider_reported_cost_usd'] for x in costs if x['provider_reported_cost_usd'] is not None),
  budget=completion['budget'],unknown_requests=sum(x['kind']=='SEND_UNKNOWN' for x in provider),source_gold_evaluations=0,independent_task_evaluations=0,experimental_operators=0,source_correctness='NOT_EVALUATED',cross_task_correctness='NOT_EVALUATED')
 save('summary.json',summary);save('operator_provenance.json',artifacts);save('request_costs.json',costs)
 save('audit.json',dict(historical_run_unchanged=all(old.values()),frozen_source_unchanged=True,raw_generated_source_exactly_executed=True,all_requests_include_all_twelve=True,no_duplicate_request_keys=True,private_scores_used=False,gold_answers_used=False,source_ids_normalized_post_response=True,freeze_sha256=freeze['protocol_sha256']))
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
