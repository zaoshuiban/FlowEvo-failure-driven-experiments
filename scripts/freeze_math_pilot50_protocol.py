"""Freeze the unapproved protocol/budgets, never sends a request."""
import json,collections,subprocess,hashlib
from pathlib import Path
from failure_evo.math_stream import read,save,sha
from failure_evo.contracts import fingerprint
from failure_evo.math_cumulative_stream import DEFAULTS
from code_math.no_gold import NoGoldPolicy
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'datasets/math_cumulative50_20261103';REPORT=ROOT/'reports/math_cumulative50_preparation_20261103'
def main():
 tasks=[json.loads(l) for l in (D/'public/tasks.jsonl').read_text().splitlines()]
 f=read(D/'freeze.json');assert all(sha(D/p)==h for p,h in f['files'].items());assert len(tasks)==50
 gate=read(D/'private/gate_pool.json');assert len(gate['cases'])==24
 per_call=88474;channels={}
 for arm in ['G','T','F','R']:
  calls={'base_solve':100,'association':49 if arm in ('T','F') else 0,'induction_code_engineering_revision':18 if arm in ('T','F') else 0,'gate_baseline_and_fallback':96 if arm in ('T','F') else 0,'R_extra':96 if arm=='R' else 0}
  channels[arm]=dict(calls=calls,total_calls_upper=sum(calls.values()),reserved_upper_microusd=sum(calls.values())*per_call,max_worker_calls=4000,max_worker_milliseconds=60000000)
 total=sum(x['total_calls_upper'] for x in channels.values());cost=total*per_call
 b=dict(version='pilot50-budget-v1',currency='USD',authorization_status='NOT_AUTHORIZED',channels=channels,total_model_calls_upper=total,total_reserved_upper_microusd=cost,
  token_reservation_per_request=73728,cost_reservation_per_request_microusd=per_call,total_tokens_upper=total*73728,
  prices=dict(model='deepseek-flash',documented_serving_family='DeepSeek-V4.1-Flash',input_cache_miss_peak_usd_per_million=.30,input_cache_hit_peak_usd_per_million=.006,output_peak_usd_per_million=1.20,source_url='https://api-docs.deepseek.com/quick_start/pricing/',snapshot_sha256=sha(REPORT/'pricing.html'),checked_on='2026-11-03',reserve='all tokens at peak output price, rounded up per request'),
  illustrative_scenario=dict(base_gate_retry_input=2048,base_gate_retry_output=2048,learning_input=12000,learning_output=4096,estimate_usd=(400+192+96)*(2048*.3+2048*1.2)/1e6+134*(12000*.3+4096*1.2)/1e6,not_forecast_or_bill=True),
  worker='local Docker; time and calls separately bounded; no invented zero compute cost',billing='actual supplier invoice unavailable; preserve estimated cost, reserved upper bound, and UNKNOWN separately',
  R_matching='v2 credits previous completed20-task window at task21/41. Matches consumed F auxiliary call counts only. Last partial window costs unmatched. No equal-token/dollar claim. No current score selection.')
 save(REPORT/'budget.json',b)
 plan=dict(version='math-cumulative50-pilot-v1',mode='DEVELOPMENT_CONTINUOUS_LEARNING',tasks_sha256=fingerprint(tasks),task_count=50,window=20,arms=['G','T','F','R'],model='deepseek-flash',solver=asdict(NoGoldPolicy(delivery_profile='concise-v1')),
  cumulative=dict(DEFAULTS,max_association_jobs=49,max_generation_jobs=6,paid_api_authorized=False),
  auxiliary_calls_per_window=48,learning_calls_per_window=32,r_policy='previous-completed-window-f-call-credit-v2',r_max_extra_calls=48,max_gate_cases=4,max_tools_per_arm=4000,
  gate_reviewers=['HOST_INDEPENDENT_REVIEW'],stop_for_gate_review=True,gate_policy='sealed-math-gate-provider-v1; review all24 by exact artifact before any Gate execution, first2supported+first2unsupported in fixed order; UNKNOWN excluded; 1 consumed Gate per exact code hash; unchanged threeGate thresholds',
  data_freeze=dict(path=str(D/'freeze.json'),sha256=sha(D/'freeze.json')),budget_freeze=b,
  source_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),dirty_worktree=True,scoring_quarantine=[],
  stops=['SEND_UNKNOWN or pending ledger','Worker failure','hash/permission/leakage error','unrecoverable partial validation','hard budget exhaustion'],
  normal_outcomes=['NEEDS_SPECIFICATION','NOT_GENERATABLE','settled delivery failure','Shadow/no independent coverage','no future match','zero benefit'],
  review_pause='At completed20/40 window, independent host semantic review required before continuing if candidate review missing. Review cannot use candidate Gate outputs or mutate code. UNKNOWN/no coverage remains Shadow; no compulsory success.',
  outcome_scope='50distinct official contest items, not independent mechanism families; all source/private-Gate provenance hostonly; performance not measured during preparation')
 save(REPORT/'plan.json',plan);print('REQUEST_UPPER',total,'USD_UPPER',cost/1e6)
if __name__=='__main__':main()
