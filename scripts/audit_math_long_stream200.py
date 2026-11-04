"""Validate frozen data and actual NoGold controller projection using mocks only."""
import sys,json,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from code_math.no_gold import PublicMathTask,NoGoldMathController,NoGoldPolicy,solver_messages
from code_math.private_math_scoring import PrivateMathScorer
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
DATA=ROOT/'datasets/math_long_stream200_20261102';OUT=ROOT/'runs/math_stream200_data_acceptance_20261102_01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
class Mock:
 def __init__(self):self.current=None;self.step=0;self.count=0
 def generate_no_gold(self,**kw):
  expected=solver_messages(self.current,None if self.step==0 else 'The answer is 0',profile='concise-v1')
  assert kw['messages']==expected
  assert set(kw)=={'messages','policy','request_id'}
  self.step+=1;self.count+=1
  return dict(text='The answer is 0',usage=dict(prompt_tokens=0,completion_tokens=0),reasoning_tokens=0,origin='MOCK',finish_reason='stop')
def main():
 OUT.mkdir(parents=True,exist_ok=False);p=read(DATA/'protocol.json');checks={}
 checks['freeze_hash']=sha(DATA/'protocol.json')==read(DATA/'freeze.json')['protocol_sha256']
 checks['all_frozen_files']=all(sha(DATA/f)==h for f,h in p['files'].items())
 old=read(ROOT/'runs/hard140_algorithm_20261028_01/protocol.json')
 checks['raw_provenance_matches_previous_freeze']=all(x['sha256']==old['raw_hashes'][s+'.parquet'] for s,x in p['raw'].items())
 tasks=lines(DATA/'public/tasks.jsonl');meta=lines(DATA/'host/task_metadata.jsonl');private=lines(DATA/'private/scoring.jsonl')
 checks['exactly_200']=len(tasks)==len(meta)==len(private)==200
 checks['unique_records']=len({x['task_id'] for x in tasks})==200
 checks['unique_template_proxies']=len({x['template_proxy_sha256'] for x in meta})==200
 checks['all_level5']=all(x['difficulty']=='Level 5' for x in meta)
 checks['seven_subjects']=len({x['subject'] for x in meta})==7
 checks['initial_preflight_and_scorer']=all(all(x['checks'].values()) for x in read(DATA/'audit/scorer_acceptance.json'))
 checks['public_allowlist']=all(set(x)=={'task_id','problem'} for x in tasks)
 checks['private_binding']=all(a['task_id']==b['task_id'] and b['problem_sha256']==fingerprint(a['problem']) for a,b in zip(tasks,private))
 c=Mock();controller=NoGoldMathController(c,OUT/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1'))
 scorer=PrivateMathScorer(private,OUT/'controller.jsonl',OUT/'private_mock_scores.jsonl')
 for i,t in enumerate(tasks):
  task=PublicMathTask.parse(t);c.current=task;c.step=0
  lock=controller.solve(task,episode_id='engineering:stream200:'+str(i),sequence=i+1)
  assert c.step==2 and lock['gold_exposed'] is False
  # Private score occurs only after Controller recorded both replies and final lock.
  scorer.score(task,lock)
 checks['controller_two_unconditional_calls_per_task']=c.count==400
 checks['only_current_task_and_previous_unverified_reply_in_requests']=True
 checks['scored_only_after_lock']=len(scorer.events.records())==200
 checks['no_published_real_results']=all(r['payload']['responses'][0]['origin']=='MOCK' for r in controller.events.records() if r['kind']=='MATH_ANSWER_LOCKED')
 summary=dict(checks=checks,passed=sum(checks.values()),total=len(checks),real_api_calls=0,mock_calls=c.count,mock_tasks=len(tasks),research_accuracy='NOT_MEASURED',note='Mock outputs do not become failure learning evidence or exposure for model-performance selection')
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));assert all(checks.values())
if __name__=='__main__':main()
