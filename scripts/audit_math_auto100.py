"""Read-only post-run freeze, visibility, ledger, permissions and cost audit."""
import json,hashlib
from run_math_auto100 import OUT,ROOT,read,sha,fingerprint
from code_math.no_gold import PublicMathTask,solver_messages
from failure_evo.evidence import EvidenceStore
from failure_evo.persistent_budget import PersistentBudget

def main():
 p=read(OUT/'protocol.json');checks=[]
 def check(name,ok):
  checks.append({'name':name,'passed':bool(ok)})
  if not ok:raise AssertionError(name)
 check('protocol hash',fingerprint(p)==read(OUT/'freeze.json')['sha256'])
 check('runtime hashes',all(sha(ROOT/f)==h for f,h in p['source_hashes'].items()))
 roles=read(OUT/'roles.json');private=read(OUT/'private.json');check('roles frozen',fingerprint(roles)==p['roles_hash']);check('private scorer frozen',fingerprint(private)==p['private_hash'])
 ids=[t['task_id'] for ts in roles.values() for t in ts];check('100 unique record IDs',len(ids)==len(set(ids))==100)
 public={t['task_id']:t for ts in roles.values() for t in ts};check('different question hashes',len({fingerprint(t['problem']) for t in public.values()})==100)
 rows=read(OUT/'results.json');seen=set();requests=0;failures=read(OUT/'failures.json')
 check('failure admission credible terminal only',all(next(r for r in rows if r['task_id']==e['task']['task_id'] and r['arm']=='Discovery')['grade']['status']=='CONFIRMED_WRONG' and e['correct'] is False for e in failures))
 for row in rows:
  l=row['locked'];check('unique episode '+l['episode_id'],l['episode_id'] not in seen);seen.add(l['episode_id'])
  path=OUT/'episodes'/row['task_id']/row['arm'];ev=EvidenceStore(path/'controller.jsonl').records();check('answer lock '+l['episode_id'],any(e['kind']=='MATH_ANSWER_LOCKED' and e['payload']==l for e in ev));check('lock hash '+l['episode_id'],fingerprint({k:v for k,v in l.items() if k!='locked_sha256'})==l['locked_sha256'])
  re=EvidenceStore(path/'requests.jsonl').records();wires={e['payload']['request_id']:e['payload'] for e in re if e['kind']=='NO_GOLD_REQUEST'};raw=[e for e in re if e['kind']=='RAW_RESPONSE'];check('requests/responses one-to-one '+l['episode_id'],len(wires)==len(raw)==l['model_calls']);requests+=len(raw)
  prev=None
  for i,response in enumerate(l['responses']):
   request=wires[l['episode_id']+'/s'+str(i)]
   check('public-only actual wire '+l['episode_id']+'/'+str(i),request['wire']['messages']==solver_messages(PublicMathTask.parse(public[row['task_id']]),prev,profile='concise-v1') and request['gold_exposed'] is False);prev=response['text']
 check('solver calls bounded',requests<=400)
 for path in OUT.rglob('budget.jsonl'):
  b=PersistentBudget.__new__(PersistentBudget);b.path=path
  with b._locked() as journal:
   states,_=b._state(journal);check('settled '+str(path.relative_to(OUT)),all(s['status']=='settled' for s in states.values()));check('monetary cap '+str(path.relative_to(OUT)),b._totals(journal)['cost']<=journal[0]['payload']['config']['max_cost_microusd'])
 lock=read(OUT/'PRE_TEST_LOCK.json');check('learning frozen during test',sha(OUT/'learning_results.json')==lock['learning_sha256'])
 for arm,h in lock['registries'].items():check('registry frozen '+arm,(sha(OUT/arm/'registry.jsonl') if (OUT/arm/'registry.jsonl').exists() else None)==h)
 if (OUT/'COMPLETE.json').exists():
  check('all scheduled solve episodes completed',len(rows)==200)
  check('60 complete trios',all(sum(r['task_id']==t['task_id'] and r['arm'] in ['G','T','F'] for r in rows)==3 for t in roles['Test']))
 result={'passed':True,'checks':len(checks),'actual_solver_responses':requests,'details':checks};(OUT/'integrity_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='details'}))
if __name__=='__main__':main()
