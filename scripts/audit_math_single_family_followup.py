import json,hashlib
from run_math_single_family_followup import OUT,ROOT,PARENT,load,sha,fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.persistent_budget import PersistentBudget
from code_math.no_gold import PublicMathTask,solver_messages

def ev(p):return EvidenceStore(p).records()
def main():
 checks=[]
 def check(name,value):
  checks.append({'name':name,'passed':bool(value)})
  if not value:raise AssertionError(name)
 p=load('protocol.json');check('frozen protocol',fingerprint(p)==load('freeze.json')['sha256']);check('frozen source',all(sha(ROOT/x)==h for x,h in p['source_hashes'].items()));check('parent frozen inputs',all(sha(PARENT/x)==h for x,h in p['parent_hashes'].items()))
 roles=load('roles.json');private=load('private.json');bundle=load('selected_bundle.json');check('role/hash binding',fingerprint(roles)==p['roles_hash'] and fingerprint(private)==p['private_hash'] and fingerprint(bundle)==p['bundle_hash'])
 old=[x for x in private if not x['task_id'].startswith('single-family-future-')];new=[x for x in private if x['task_id'].startswith('single-family-future-')];check('30 new parameters',len(new)==30 and not {fingerprint([x['family'],x['parameters']]) for x in old}&{fingerprint([x['family'],x['parameters']]) for x in new})
 check('original failure records unchanged',all(e in json.loads((PARENT/'failures.json').read_text()) for e in bundle['events']))
 artifacts={}
 for arm in ['T','F']:
  provider=ev(OUT/arm/'provider.jsonl');first=next(x['payload']['wire'] for x in provider if x['kind']=='SEND_STARTED');view=json.loads(first['messages'][1]['content'])['evidence'];check('neutral source-selection '+arm,'failure' not in view['selection']);check('only F gets trajectories '+arm,('observations' in view)==(arm=='F'));check('same source questions '+arm,view['questions']==[{'problem':e['task']['problem']} for e in bundle['events']])
  pe=ev(OUT/arm/'pipeline/learning.jsonl');reviews=[x['payload'] for x in pe if x['kind']=='DEVELOPMENT_REVIEW']
  for r in reviews:
   a=r['artifact'];artifacts[a['code_sha256']]=a;code=open(a['source_path']).read();check('exact code hash '+arm,hashlib.sha256(code.encode()).hexdigest()==a['code_sha256'])
   raw=next(x['payload']['response'] for x in provider if x['kind']=='RAW_RESPONSE' and fingerprint(x['payload']['response'])==a['response_sha256']);check('actual model source, not host replacement '+arm,json.loads(raw['choices'][0]['message']['content'])['code']==code and a['origin']=='DEEPSEEK')
  for x in ev(OUT/arm/'registry.jsonl'):
   if x['kind']=='MATH_EXPERIMENTAL':
    v=x['payload']['validation'];check('actual bound Gate receipt '+arm,any(e['kind']=='GATE_DECISION' and e['payload']==v for e in pe));check('Gate correctness '+arm,v['gate_passed'] and any(e['correct'] for e in v['gate_rows']) and not any(e['status']=='ERROR' or e['status']=='APPLIED' and not e['correct'] for e in v['gate_rows']))
 public={t['task_id']:t for t in roles['Test']};rows=load('results.json') if (OUT/'results.json').exists() else [];seen=set();requests=0
 for row in rows:
  l=row['locked'];path=OUT/'episodes'/row['task_id']/row['arm'];check('unique episode '+l['episode_id'],l['episode_id'] not in seen);seen.add(l['episode_id']);check('locked answer '+l['episode_id'],any(x['kind']=='MATH_ANSWER_LOCKED' and x['payload']==l for x in ev(path/'controller.jsonl')));check('lock integrity '+l['episode_id'],fingerprint({k:v for k,v in l.items() if k!='locked_sha256'})==l['locked_sha256'])
  if l['selection']=='first_applied_operator':check('no gold-triggered rescue '+l['episode_id'],l['model_calls']==0 and l['operator_events'][-1]['code_sha256'] in artifacts)
  wire={x['payload']['request_id']:x['payload']['wire'] for x in ev(path/'requests.jsonl') if x['kind']=='NO_GOLD_REQUEST'};requests+=len(wire);check('response count '+l['episode_id'],len(wire)==l['model_calls']);prev=None
  for i,r in enumerate(l['responses']):
   check('public-only wire '+l['episode_id']+str(i),wire[l['episode_id']+'/s'+str(i)]['messages']==solver_messages(PublicMathTask.parse(public[row['task_id']]),prev,profile='concise-v1'));prev=r['text']
 for path in OUT.rglob('budget.jsonl'):
  b=PersistentBudget.__new__(PersistentBudget);b.path=path
  with b._locked() as log:
   states,_=b._state(log);check('all requests settled '+str(path),all(x['status']=='settled' for x in states.values()));check('within money cap '+str(path),b._totals(log)['cost']<=log[0]['payload']['config']['max_cost_microusd'])
 lock=load('PRE_TEST_LOCK.json');check('learning frozen',lock['learning_sha256']==sha(OUT/'learning_results.json'))
 for a,h in lock['registries'].items():check('registry frozen '+a,h==(sha(OUT/a/'registry.jsonl') if (OUT/a/'registry.jsonl').exists() else None))
 if load('COMPLETE.json')['status']=='COMPLETE':check('30 full pairs',len(rows)==90 and all(sum(r['task_id']==t['task_id'] for r in rows)==3 for t in roles['Test']))
 result=dict(passed=True,checks=len(checks),solver_requests=requests,details=checks);(OUT/'integrity_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items() if k!='details'})
if __name__=='__main__':main()
