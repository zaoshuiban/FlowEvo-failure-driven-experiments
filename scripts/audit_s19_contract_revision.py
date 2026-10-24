"""Offline saved-response replay and scheduler audit. Never imports a model sender."""
import argparse,copy,json,subprocess,hashlib
from pathlib import Path
import run_workflow_v2 as e
from run_learning_stream import packet_check,restore_budget
from failure_evo.contracts import fingerprint,strict_feedback
from failure_evo.learning_contract import normalize
from failure_evo.repair_choice_v2 import choose,generic_choice
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.evidence import EvidenceStore

BASE='ed28e6e9c6478329074ba959c9b1b6d708e785d0'
OLD=e.ROOT/'runs/s19_real_pilot_20261024_01'
def hashes(root):return {str(p.relative_to(root)):e.sha(p) for p in root.rglob('*') if p.is_file()}
def main(output):
 out=Path(output);out.mkdir(parents=True,exist_ok=False);before=hashes(OLD)
 plan=e.read(e.ROOT/'reports/s19_real_pilot_20261024_01/plan.json');baseline=[]
 for f,sha in plan['frozen_files'].items():
  path=e.ROOT/f
  git=subprocess.run(['git','show',BASE+':'+f],cwd=e.ROOT,capture_output=True)
  raw=git.stdout if git.returncode==0 else path.read_bytes()
  baseline.append(dict(path=f,pilot_sha256=sha,baseline_sha256=hashlib.sha256(raw).hexdigest(),matches=hashlib.sha256(raw).hexdigest()==sha,origin='git baseline' if git.returncode==0 else 'unchanged local frozen file'))
 assert all(x['matches'] for x in baseline)
 # HEAD contains only the previous Pilot report commit, not source edits.
 committed_diff=subprocess.check_output(['git','diff',BASE,'HEAD','--','FlowEvo','scripts'],cwd=e.ROOT,text=True)
 assert not committed_diff
 e.write(out/'baseline.json',dict(source_commit=BASE,prechange_committed_source_identical=True,dependencies=baseline))
 receipts=e.read(OLD/'learning_requests.json');replays=[]
 for rp in sorted((OLD/'jobs').glob('*/*-response.json')):
  slot=rp.name.split('-')[0];messages=e.read(rp.parent/f'{slot}-messages.json');response=e.read(rp)
  receipt=next(x for x in receipts if x['request_id']==rp.parent.name+f'/generate/{slot}')
  wires=[p for p in (OLD/'wire').rglob('request.json') if e.sha(p)==receipt['request_sha256']]
  assert len(wires)==1
  wire=e.read(wires[0]);assert wire['messages']==messages
  material=json.loads(messages[-1]['content']);packets=[packet_check(p) for p in material['source_packets']]
  audit=normalize(response['text'],response['finish_reason']);assert audit['accepted']
  comparisons=[]
  for p in packets:
   b=restore_budget(p['checkpoint_budget']);f=strict_feedback(p['feedback']);a=choose(audit['normalized']['rule'],p['code'],f,b);g=generic_choice(p['code'],f,b)
   comparisons.append(dict(task_id=p['task_id'],event_id=p['event_id'],action=a,generic_action=g,same_action=a==g))
  item=dict(audit,original_response_path=str(rp.relative_to(e.ROOT)),response_sha256=e.sha(rp),request_sha256=e.sha(wires[0]),request_path=str(wires[0].relative_to(e.ROOT)),full_request_matches=True,original_diagnosis=e.read(rp.parent/'state.json')['diagnosis'],source_action_comparison=comparisons,posthoc_only=True,registered=False)
  e.write(out/f'replay-{len(replays)+1}.json',item);replays.append(item)
 e.write(out/'replay_summary.json',dict(real_api_calls=0,responses=len(replays),complete_protocol_passed=sum(x['accepted'] for x in replays),distinct_rules=len({x['rule_sha256'] for x in replays}),responses_same_as_generic=sum(all(c['same_action'] for c in x['source_action_comparison']) for x in replays),status='NO_DISTINCT_ACTION_VALUE',old_result='0/4 unchanged',registered=0))
 # Reconstruct only states visible at each OLD schedule boundary, in a fresh audit tree.
 hrows=EvidenceStore(OLD/'hypotheses.jsonl').records();times=sorted({r['at'] for r in hrows if r['kind']=='SCHEDULE_DECISION'})
 for n,at in enumerate(times):
  path=out/f'scheduler-{n+1}.jsonl';events=EvidenceStore(path)
  for row in hrows:
   if row['at']<=at and row['kind']!='SCHEDULE_DECISION' and row['kind']!='JOB_SCHEDULED':events.append(row['kind'],row['payload'],row['at'])
  store=FailureEvidenceStore(OLD/'evidence_F.jsonl')
  index=SymptomLearning(path,store,plan['run_id']+'-F','repair-choice-json-v2',scheduler_protocol='evidence-diversity-v1')
  prior_decisions=[r['payload'] for r in hrows if r['kind']=='SCHEDULE_DECISION' and r['at']==at]
  available=not all(j['reason']=='NO_BUDGET' for j in prior_decisions)
  jobs=index.schedule(at=at,budget_available=available)
  e.write(out/f'scheduler-{n+1}-summary.json',dict(posthoc_only=True,at=at,budget_available=available,new_jobs=jobs,old_decisions=prior_decisions))
 after=hashes(OLD);assert before==after
 e.write(out/'old_run_integrity.json',dict(unchanged=True,files=len(before),sha256=fingerprint(before),files_sha256=before))
 print(json.dumps(e.read(out/'replay_summary.json'),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();main(a.output)
