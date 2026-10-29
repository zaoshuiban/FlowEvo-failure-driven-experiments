"""Build P0 provenance and proposal; no model transport imports or paid requests."""
import hashlib,json,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint
from code_math.private_math_scoring import normalized
from failure_evo.math_learning import CONTRACT,HYPOTHESIS_SCHEMA
from code_math.no_gold import SOLVER_SYSTEM,REVIEW_SYSTEM
out=ROOT/'reports/math_no_gold_p0_20261027';data=out/'data'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):(out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
files=['README.md','.gitignore','FlowEvo/src/code_math/loader.py','FlowEvo/src/code_math/runner.py','FlowEvo/src/runtime/llm_client.py',
 'FlowEvo/src/code_math/no_gold.py','FlowEvo/src/code_math/private_math_scoring.py','FlowEvo/src/failure_evo/math_operators.py','FlowEvo/src/failure_evo/math_transport.py','FlowEvo/src/failure_evo/math_learning.py',
 'scripts/freeze_math_no_gold.py','scripts/accept_math_no_gold.py','scripts/tests/test_math_no_gold.py','scripts/report_math_no_gold_p0.py']
dependencies=[str(p.relative_to(ROOT)) for folder in ('FlowEvo/src/failure_evo','FlowEvo/src/code_math','FlowEvo/src/runtime','FlowEvo/src/core','FlowEvo/src/env','FlowEvo/src/eval') for p in (ROOT/folder).rglob('*.py')]
worker='experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
manifest=dict(base_commit=base,expected_base='abf86c669ab5d5a2f8419085b43db6f813c74741',new_commit_created=False,changed_files={f:sha(ROOT/f) for f in files},dependencies={f:sha(ROOT/f) for f in sorted(set(dependencies+[worker]))},python=sys.version,platform=platform.platform(),dataset_manifest_sha256=sha(data/'manifest.json'))
write('source_manifest.json',manifest)
price=dict(checked_on='2026-10-27',currency='USD',unit='per_million_tokens',openai=dict(model='gpt-5.4-2026-03-05',input=2.5,cached_input=.25,output=15,source='https://developers.openai.com/api/docs/models/gpt-5.4'),deepseek=dict(model='deepseek-flash',documented_version='DeepSeek-V4.1-Flash-1017',input_peak_cache_miss=.30,input_peak_cache_hit=.006,output_peak=1.2,source='https://api-docs.deepseek.com/quick_start/pricing/'),billing_note='quote-based upper estimates, not invoice; no caching/off-peak discount assumed')
write('pricing_snapshot.json',price)
solver_calls=192+3*1440*2
gpt_calls=2*7
budget=dict(authorized=False,paid_requests_p0=0,solver=dict(model='deepseek-flash',discovery_calls_max=192,formal_calls_max=8640,total_calls_max=solver_calls,input_upper=32768,output_upper=4096,
    quote_directional_upper_usd=solver_calls*(32768*.30+4096*1.2)/1e6,persistent_reservation_upper_usd=solver_calls*(32768+4096)*1.2/1e6),
 generation=dict(model='gpt-5.4-2026-03-05',calls_max=gpt_calls,per_arm_calls_max=7,input_upper=65536,output_upper=8192,
    quote_directional_upper_usd=gpt_calls*(65536*2.5+8192*15)/1e6,persistent_reservation_upper_usd=gpt_calls*(65536+8192)*15/1e6),
 local=dict(max_operator_invocations=2*(6*(6+48+2)+48)+2*1440,max_worker_seconds_each=2,reserved_wall_milliseconds_each=20000,cost_monetized=False),
 auxiliary=dict(enabled=False,M_additional_solver_calls_max=2880,O_additional_solver_calls_max=2880,additional_learning_calls='must freeze separately; no old O restoration authorized'))
budget['quote_directional_total_upper_usd']=budget['solver']['quote_directional_upper_usd']+budget['generation']['quote_directional_upper_usd']
budget['persistent_reservation_total_upper_usd']=budget['solver']['persistent_reservation_upper_usd']+budget['generation']['persistent_reservation_upper_usd']
budget['proposed_independent_hard_caps_usd']=dict(P1_discovery=9,P2_T_generation=8,P2_F_generation=8,P4_formal_solver=383)
# Rounded per-channel caps exceed conservative existing ledger occupancy, not expected expenditure.
write('budget_proposal.json',budget)
protocol=dict(version='math-no-gold-p0-proposal-v1',status='ENGINEERING_ACCEPTED_AWAITING_NEW_AUTHORIZATION',source_manifest_sha256=sha(out/'source_manifest.json'),dataset_manifest_sha256=sha(data/'manifest.json'),budget_sha256=sha(out/'budget_proposal.json'),
 solver=dict(model='deepseek-flash',temperature=0,thinking=False,output_tokens=4096,input_upper=32768,reflection_calls=1,reflection_trigger='unconditional fixed schedule, no score',selection='last scheduled response; first APPLIED operator locks without rescue'),
 compiler=dict(model='gpt-5.4-2026-03-05',reasoning='medium',contract_sha256=hashlib.sha256(CONTRACT.encode()).hexdigest(),schema_sha256=fingerprint(HYPOTHESIS_SCHEMA),max_candidates_per_arm=3,max_revisions_per_candidate=1,selection='first source+Design pass, stop generating, freeze one winner per arm before Gate; never replace after Gate failure',source_selection='earliest up to6 distinct terminal numeric failures; no class filtering',context_fragment_characters=2400,context_full_source_hashes=True,max_wire_upper=65536),
 admissibility=dict(source='at least one correct applied; no incorrect applied or ERROR',design='same',gate='same; no feedback to generation',refusal='all declines and errors logged; all public questions supplied, no labels'),
 worker=dict(image='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8',script=worker,sha256=sha(ROOT/worker),network='none',read_only=True,user='65534:65534',memory='256m',cpus=1,pids=32,timeout_seconds=2,mounts=['generated candidate','frozen Worker']),
 solver_system_sha256=hashlib.sha256(SOLVER_SYSTEM.encode()).hexdigest(),review_system_sha256=hashlib.sha256(REVIEW_SYSTEM.encode()).hexdigest(),
 primary_arms=['G','T','F'],auxiliary_arms_enabled=False,formal_order='frozen schedule role/seed/task/repeat; arm order cyclic GTF/TFG/FGT by task ordinal',
 failure_learning='Discovery only, terminal private grade without gold; rational mismatch only; UNVERIFIED_NONMATCH excluded',
 test_feedback='none to learner or router; score after answer lock; formal versions remain frozen',
 stopping=['gold leakage','permission violation','data contamination','UNKNOWN request','Worker infrastructure fault','budget exhaustion'],
 no_mechanism_is_valid=True,old_budgets_reused=False,paid_api_authorized=False)
write('protocol.json',protocol)
coverage={}
for role in ('discovery','design','gate','legacy_test','fresh_test'):
 rows=[json.loads(x) for x in (data/'private'/(role+'.jsonl')).read_text().splitlines()]
 n=sum(normalized(r['gold_answer'])[0]=='rational' for r in rows)
 coverage[role]=dict(total=len(rows),rational_reference=n,symbolic_or_text_reference=len(rows)-n)
write('scoring_coverage.json',coverage)
summary=json.loads((out/'acceptance04/summary.json').read_text())
write('p0_summary.json',dict(status='P0_ENGINEERING_PASS_P1_REQUIRES_NEW_AUTHORIZATION',real_model_requests=0,real_learned_operators=0,tests=summary,protocol_sha256=sha(out/'protocol.json'),dataset_counts=json.loads((data/'manifest.json').read_text())['counts'],legacy_regression=dict(run=17,passed=12,skipped=5),scoring_coverage=coverage,limitations=['symbolic nonmatch is not a credible failure','historically targeted distribution; not natural all-math distribution','fresh seeds do not prove never exposed across every historical project','Gate test coverage is not applicability proof','real provider access and model learning untested','M/O auxiliary arms not activated']))
print(json.dumps(dict(budget=budget,coverage=coverage,protocol_sha256=sha(out/'protocol.json')),ensure_ascii=False,indent=2))
