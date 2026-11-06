"""Synthetic frozen journals; no real models, research claims or source execution."""
import copy,json,tempfile,unittest
from pathlib import Path
from analyze_math_reuse_outcomes import fp,sha,freeze,analyze,ratio,source_version

class AuditTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name);self.root=self.base/'run';self.root.mkdir()
  self.tasks=[dict(task_id=k,problem='public problem '+k) for k in ('a','b','c')]
  self.lineage={k:dict(source_original_id='o'+str(i),lineage_id='l'+str(i),source_identity_verified=True,prior_exposure=False) for i,k in enumerate(('a','b','c'),1)}
  self.protocol=json.loads((Path(__file__).resolve().parents[1]/'docs/research_evaluation/math_outcome_protocol_v1.json').read_text())
  self.protocol['prices_usd_per_million']={c:dict(input_uncached=1,input_cached=.1,output=2) for c in ('solve_base','solve_extra','learning','validation')};self.protocol['worker_usd_per_second']=.1
  self.status={'G':[True,False,False],'T':[True,False,True],'F':[True,True,True],'R':[True,False,False]};self.mock=False;self.prospective=False;self.events={};self.build()
 def write(self,path,rows):
  p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);previous='0'*64;lines=[]
  for i,(kind,payload) in enumerate(rows):
   r=dict(kind=kind,payload=payload,at=float(i),previous_hash=previous);r['record_hash']=fp(r);previous=r['record_hash'];lines.append(json.dumps(r))
  p.write_text(('\n'.join(lines)+'\n') if lines else '');self.events[path]=copy.deepcopy(rows)
 def add(self,path,kind,payload):self.write(path,self.events[path]+[(kind,payload)])
 def build(self):
  self.events={};self.root.mkdir(exist_ok=True)
  plan={'tasks_sha256':fp(self.tasks)}
  if self.prospective:
   plan['analysis_protocol_sha256']=fp(self.protocol);plan['analysis_implementation_sha256']=sha((Path(__file__).parent/'analyze_math_reuse_outcomes.py').read_bytes())
  self.write('stream.jsonl',[('STREAM_FROZEN',plan),('STREAM_COMPLETED',{'paid_api':not self.mock})])
  code='def solve(p): return "1"\n'
  a=dict(code=code,code_sha256=sha(code.encode()),operator_contract={'source_evidence':['e1','e2'],'artifact_kind':'REUSABLE_CANDIDATE'},source_evidence_ids=['e1','e2'],source_original_ids=['o1','o2'],generation_protocol='fixture',excluded_task_ids=['a','b'],origin='MOCK' if self.mock else 'DEEPSEEK')
  a['candidate_version']=source_version(a);self.artifact=a
  self.result=dict(status='APPLIED',answer='1',code_sha256=a['code_sha256'])
  for arm in ('G','T','F','R'):
   states=[];controls=[];grades=[];requests=[];budget=[('RUN_OPENED',{'config':{'run_id':'run-'+arm}})]
   for n,t in enumerate(self.tasks,1):
    status=self.status[arm][n-1];applied=arm=='F' and n==3
    finish='length' if status=='TRUNCATED' else 'stop'
    lock=dict(task_id=t['task_id'],sequence=n,episode_id=arm+'/'+str(n),final_output='The answer is 1',responses=[] if applied else [dict(finish_reason=finish)],operator_events=[self.result] if applied else [],protocol='fixture')
    lock['locked_sha256']=fp(lock)
    grade=dict(task_id=t['task_id'],locked_sha256=lock['locked_sha256'],status='CONFIRMED_CORRECT' if status is True else 'CONFIRMED_WRONG' if status is False else status,correct=status if type(status) is bool else None,scorer_version='math-stream-strict-v1')
    states += [('ANSWER_LOCKED',dict(task_id=t['task_id'],sequence=n,id=arm+'/'+str(n),lock=lock)),('PRIVATE_SCORED',dict(task_id=t['task_id'],sequence=n,verdict=grade))]
    controls += [('MATH_TASK_STARTED',dict(task_id=t['task_id'],problem_sha256=fp(t['problem']),policy={'temperature':0,'operators_enabled':arm in ('T','F')})),('MATH_ANSWER_LOCKED',lock)]
    grades.append(('MATH_PRIVATE_SCORE',grade))
    if not applied:
     rid=arm+'/'+str(n);u=dict(prompt_tokens=20,completion_tokens=10,prompt_cache_hit_tokens=5,prompt_cache_miss_tokens=15,completion_tokens_details={'reasoning_tokens':3})
     requests += [('NO_GOLD_REQUEST',dict(origin='MOCK' if self.mock else 'DEEPSEEK')),('RAW_RESPONSE',dict(request_id=rid,response=dict(id=rid,choices=[{'finish_reason':finish}],usage=u)))]
     budget += [('RESERVED',dict(request_id=rid,kind='model',cost_upper_microusd=99999,tool_milliseconds_upper=0)),('SETTLED',dict(request_id=rid,tokens=30))]
   budget += [('RESERVED',dict(request_id='tool',kind='tool',cost_upper_microusd=0,tool_milliseconds_upper=1000)),('SETTLED',dict(request_id='tool',tool_milliseconds=500))]
   for name,rows in [('task_state.jsonl',states),('controller.jsonl',controls),('scores.jsonl',grades),('requests.jsonl',requests),('solve_budget.jsonl',budget)]:self.write(arm+'/'+name,rows)
   reg=[]
   if arm=='F':
    reg=[('MATH_SHADOW',a),('MATH_EXPERIMENTAL',dict(artifact=a,effective_after=2)),('V3_TRIAL_AUTHORIZATION',dict(candidate_version=a['candidate_version'],task_ids=['c'],max_uses=1,effective_after=2)),('MATH_ROUTER_PUBLICATION',dict(artifact=a,passed=True)),('V3_TRIAL_RESERVED',dict(candidate_version=a['candidate_version'],code_sha256=a['code_sha256'],task_id='c',sequence=3)),('MATH_ROUTER_EXECUTED',dict(code_sha256=a['code_sha256'],task_id='c',sequence=3,result=self.result))]
   self.write(arm+'/registry.jsonl',reg)
  self.refresh()
 def refresh(self):
  for name,value in [('tasks',self.tasks),('lineage',self.lineage),('protocol',self.protocol)]:
   (self.base/(name+'.json')).write_text(json.dumps(value))
  self.manifest=self.base/'snapshot.json';freeze(self.root,self.base/'tasks.json',self.base/'lineage.json',self.base/'protocol.json',self.manifest)
 def result_of(self):return analyze(self.manifest)
 def test_zero_success_on_verified_reuse_is_evaluable(self):
  self.status['F'][2]=False;self.build();r=self.result_of()['arms']['F']['reuse']['independent_successes']
  self.assertEqual(r['status'],'EVALUABLE_CONDITIONAL_ON_FROZEN_LINEAGE');self.assertEqual(r['distinct_originals'],0)
 def test_false_accept_false_refuse_and_unknown_separated(self):
  cases=[dict(task_id='v'+str(i),problem='validation '+str(i),supported=v) for i,v in enumerate([False,True,True])]
  package=dict(origin='SYNTHETIC_TEST_ONLY',artifact_sha256=self.artifact['code_sha256'],candidate_version=self.artifact['candidate_version'],Development=[],Gate=cases)
  path=self.root/'F/learning/job/reviewed_cases.private.json';path.parent.mkdir(parents=True);path.write_text(json.dumps(package))
  rows=[dict(problem_sha256=fp(c['problem']),observation={'match':{'status':status}},combined='FALSE_ACCEPT',applicability=status) for c,status in zip(cases,['MATCH','DECLINE','UNKNOWN'])]
  self.add('F/registry.jsonl','V3_VALIDATION',dict(code_sha256=self.artifact['code_sha256'],candidate_version=self.artifact['candidate_version'],role='Gate',data_hash=fp(cases),rows=rows));self.refresh()
  table=self.result_of()['arms']['F']['applicability']['by_role']['Gate']
  self.assertEqual(table['false_accept'],1);self.assertEqual(table['false_refuse'],1);self.assertEqual(table['supported_unknown'],1);self.assertEqual(table['supported_missed'],2)
 def test_private_output_in_other_git_repo_rejected(self):
  import subprocess
  from analyze_math_reuse_outcomes import external_output
  repo=self.base/'other-repo';repo.mkdir();subprocess.run(['git','init'],cwd=repo,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  with self.assertRaises(ValueError):external_output(repo/'analysis.json',self.root)
 def test_freeze_cannot_overwrite_reference(self):
  with self.assertRaises(ValueError):freeze(self.root,self.base/'tasks.json',self.base/'lineage.json',self.base/'protocol.json',self.base/'tasks.json')
 def test_fixed_pairs(self):
  r=self.result_of();self.assertEqual(r['comparisons_F_minus']['G']['net_correct_tasks'],2);self.assertEqual(r['comparisons_F_minus']['T']['net_correct_tasks'],1);self.assertEqual(r['comparisons_F_minus']['R']['net_correct_tasks'],2)
 def test_independent_reuse_distinct_original(self):
  r=self.result_of()['arms']['F']['reuse'];self.assertEqual(r['independent_successes']['distinct_originals'],1);self.assertEqual(r['applied_workflow_pairs_vs_G']['left_only'],1)
 def test_same_checkpoint_not_claimed(self):self.assertIsNone(self.result_of()['arms']['F']['reuse']['same_checkpoint_causal_pairs']['count'])
 def test_unknown_identity_not_independent(self):
  self.lineage['c']['source_identity_verified']=False;self.refresh();self.assertIsNone(self.result_of()['arms']['F']['reuse']['independent_successes']['distinct_originals'])
 def test_parameter_lineage_overlap_excluded(self):
  self.lineage['c']['lineage_id']='l1';self.refresh();self.assertIn('SOURCE_OR_PARAMETER_LINEAGE_OVERLAP',self.result_of()['arms']['F']['reuse']['excluded_independence_reasons'])
 def test_repeated_original_grouped(self):
  self.lineage['b']['source_original_id']='o1';self.lineage['b']['lineage_id']='l1';self.refresh();self.assertEqual(self.result_of()['comparisons_F_minus']['G']['verified_originals'],2)
 def test_mock_cannot_become_research_gain(self):
  self.mock=True;self.build();r=self.result_of();self.assertEqual(r['research_scope'],'ENGINEERING_ONLY');self.assertIsNone(r['arms']['F']['reuse']['independent_successes']['distinct_originals'])
 def test_shadow_pairs_require_native_and_private_receipts(self):
  native=self.events['F/task_state.jsonl'][0][1]['lock']
  eid='shadow-a'
  lock=dict(task_id='a',episode_id=eid,operator_events=[self.result])
  lock['locked_sha256']=fp(lock)
  score=dict(task_id='a',locked_sha256=lock['locked_sha256'],status='CONFIRMED_WRONG',
   correct=False,scorer_version='math-stream-strict-v1')
  version=self.artifact['candidate_version']
  self.add('F/registry.jsonl','CONTRACT_SHADOW_EXECUTED',dict(
   execution_id=eid,sequence=1,task_id='a',binding=version,result=self.result))
  self.add('F/registry.jsonl','OPERATOR_VALIDATOR_EXECUTED',dict(
   stage='SHADOW_OBSERVATION',execution_id=eid,binding=version,score=score,
   result_manifest_sha256=fp([self.result,score]),baseline_result_reference=native['locked_sha256']))
  self.write('F/private/contract_shadow/controller.jsonl',[('MATH_ANSWER_LOCKED',lock)])
  score_path='F/private/contract_shadow/scores.jsonl'
  self.write(score_path,[('MATH_PRIVATE_SCORE',score)])
  self.refresh()
  result=self.result_of()
  self.assertEqual(result['task_outcomes'][0]['arms']['F'],'CONFIRMED_CORRECT')
  self.assertEqual(result['shadow_native_pairs']['F']['comparison']['right_only'],1)
  self.assertIsNotNone(result['comparisons_F_minus']['G']['original_effect_interval']['bounds'])
  self.write(score_path,[])
  self.refresh()
  with self.assertRaisesRegex(ValueError,'unbound Shadow/native pair'):
   self.result_of()
 def test_missing_and_truncated_not_math_wrong(self):
  self.status['G'][1]='TRUNCATED';self.build();r=self.result_of();self.assertEqual(r['common_confirmed_tasks'],2);self.assertEqual(r['arms']['G']['status_counts']['TRUNCATED'],1)
 def test_zero_denominator(self):self.assertIsNone(ratio(0,0)['value'])
 def test_drift_rejected(self):
  with (self.root/'F/scores.jsonl').open('a') as f:f.write('\n')
  with self.assertRaises(ValueError):self.result_of()
 def test_hash_chain_corruption_rejected(self):
  path=self.root/'F/scores.jsonl';r=json.loads(path.read_text().splitlines()[0]);r['payload']['status']='CONFIRMED_WRONG';path.write_text(json.dumps(r)+'\n');self.refresh()
  with self.assertRaises(ValueError):self.result_of()
 def test_analysis_does_not_modify_inputs(self):
  before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()};self.result_of();after={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()};self.assertEqual(before,after)
 def test_duplicate_raw_response_not_double_charged(self):
  rows=self.events['G/requests.jsonl'];self.add('G/requests.jsonl',*next(r for r in rows if r[0]=='RAW_RESPONSE'));self.refresh();self.assertEqual(self.result_of()['arms']['G']['costs']['observed_responses'],3)
 def test_all_tokens_and_worker_cost(self):
  c=self.result_of()['arms']['G']['costs'];self.assertEqual(c['channels']['solve_base']['output_tokens'],30);self.assertEqual(c['channels']['solve_base']['reasoning_tokens'],9);self.assertAlmostEqual(c['estimated_model_usd'],.0001065);self.assertAlmostEqual(c['estimated_worker_usd'],.05)
 def test_unknown_reservation_separate(self):
  self.add('G/solve_budget.jsonl','RESERVED',dict(request_id='unknown',kind='model',cost_upper_microusd=12345,tool_milliseconds_upper=0));self.add('G/solve_budget.jsonl','UNKNOWN',{'request_id':'unknown'});self.refresh();c=self.result_of()['arms']['G']['costs'];self.assertEqual(c['unknown_or_pending_reserved_microusd'],12345);self.assertIsNone(c['total_estimated_usd'])
 def test_no_prices_not_free(self):
  self.protocol['prices_usd_per_million']=None;self.refresh();self.assertIsNone(self.result_of()['arms']['G']['costs']['estimated_model_usd'])
 def test_posthoc_and_prospective_distinguished(self):
  self.assertEqual(self.result_of()['analysis_status'],'EXPLORATORY_POSTHOC_OR_ENGINEERING');self.prospective=True;self.build();self.assertEqual(self.result_of()['analysis_status'],'PROSPECTIVE_PLAN_BOUND_TO_RUN')
 def test_foreign_problem_not_paired(self):
  rows=self.events['G/controller.jsonl'];rows[0][1]['problem_sha256']='wrong';self.write('G/controller.jsonl',rows);self.refresh()
  with self.assertRaises(ValueError):self.result_of()
 def test_old_admission_does_not_verify_new_contract(self):
  rows=self.events['F/registry.jsonl'];rows[1][1]['artifact']=copy.deepcopy(self.artifact);rows[1][1]['artifact']['operator_contract']['source_evidence'].append('changed');self.write('F/registry.jsonl',rows);self.refresh();self.assertIn('NO_PRIOR_ADMISSION',self.result_of()['arms']['F']['reuse']['excluded_independence_reasons'])
if __name__=='__main__':unittest.main()
