"""Read-only frozen-outcome audit. No runtime registry, scorer, model or lock writer imports."""
import argparse,collections,hashlib,json,math,os,subprocess
from decimal import Decimal
from pathlib import Path

VERSION='math-readonly-outcome-audit-v1'
ARMS=('G','T','F','R')
CONFIRMED={'CONFIRMED_CORRECT','CONFIRMED_WRONG'}

def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fp(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()
def ratio(n,d):return dict(numerator=n,denominator=d,value=n/d if d else None,status='EVALUABLE' if d else 'NOT_EVALUABLE_ZERO_DENOMINATOR')
def sign_p(w,l):
 n=w+l
 return min(1.0,2*sum(math.comb(n,k) for k in range(min(w,l)+1))/(2**n)) if n else 1.0

def journal(data):
 if data and not data.endswith(b'\n'):raise ValueError('partial journal')
 previous='0'*64;rows=[]
 for line in data.splitlines():
  r=json.loads(line)
  if type(r.get('at')) not in (int,float) or not math.isfinite(r['at']) or rows and r['at']<rows[-1]['at']:raise ValueError('invalid event time order')
  raw={k:v for k,v in r.items() if k!='record_hash'}
  if r.get('previous_hash')!=previous or fp(raw)!=r.get('record_hash'):raise ValueError('journal integrity failure')
  previous=r['record_hash'];rows.append(r)
 return rows

def inventory(root):
 return sorted(p for p in root.rglob('*') if p.is_file() and (p.suffix in ('.jsonl','.py') or p.name=='reviewed_cases.private.json'))
def external_output(path,root):
 path=Path(path).resolve()
 if path==root or root in path.parents:raise ValueError('output must be outside input Run')
 git=subprocess.run(['git','-C',str(root),'rev-parse','--show-toplevel'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 if git.returncode==0:
  repo=Path(git.stdout.strip()).resolve()
  if path==repo or repo in path.parents:raise ValueError('private analysis output must be outside Git repository')
 parent=path.parent
 while not parent.exists():parent=parent.parent
 destination_git=subprocess.run(['git','-C',str(parent),'rev-parse','--show-toplevel'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 if destination_git.returncode==0:raise ValueError('private analysis output must be outside every Git repository')
 path.parent.mkdir(parents=True,exist_ok=True)
 return path

def private_write(path,text):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f:
  os.fchmod(f.fileno(),0o600);f.write(text)


def freeze(root,tasks,lineage,protocol,output):
 root=Path(root).resolve();output=external_output(output,root)
 files=inventory(root)
 if any(p.is_symlink() for p in root.rglob('*')):raise ValueError('symlink input requires explicit audit')
 refs={name:dict(path=str(Path(p).resolve()),sha256=sha(Path(p).read_bytes())) for name,p in [('tasks',tasks),('lineage',lineage),('protocol',protocol)]}
 if output in {Path(r['path']).resolve() for r in refs.values()}:raise ValueError('cannot overwrite source references')
 manifest=dict(version=VERSION,root=str(root),files=[dict(path=str(p.relative_to(root)),sha256=sha(p.read_bytes())) for p in files],references=refs)
 private_write(output,json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 return manifest

class Snapshot:
 def __init__(self,path):
  self.manifest_bytes=Path(path).read_bytes();self.manifest=json.loads(self.manifest_bytes)
  if self.manifest['version']!=VERSION:raise ValueError('snapshot protocol version')
  self.root=Path(self.manifest['root']).resolve();self.bytes={};self.logs={}
  for r in self.manifest['files']:
   rel=Path(r['path'])
   if rel.is_absolute() or '..' in rel.parts or r['path'] in self.bytes:raise ValueError('snapshot path')
   p=self.root/rel
   if p.is_symlink() or sha(p.read_bytes())!=r['sha256']:raise ValueError('snapshot drift: '+str(rel))
   data=p.read_bytes();self.bytes[str(rel)]=data
   if p.suffix=='.jsonl':self.logs[str(rel)]=journal(data)
  self.refs={}
  for k,r in self.manifest['references'].items():
   data=Path(r['path']).read_bytes()
   if sha(data)!=r['sha256']:raise ValueError('reference drift: '+k)
   self.refs[k]=json.loads(data) if not r['path'].endswith('.jsonl') else [json.loads(l) for l in data.splitlines()]
  self.verify()
 def verify(self):
  if {str(p.relative_to(self.root)) for p in inventory(self.root)}!=set(self.bytes):raise ValueError('input inventory drift')
  for p,data in self.bytes.items():
   if (self.root/p).read_bytes()!=data:raise ValueError('input changed during analysis')
  for r in self.manifest['references'].values():
   if sha(Path(r['path']).read_bytes())!=r['sha256']:raise ValueError('reference changed during analysis')
 def events(self,arm,name):return self.logs.get(arm+'/'+name,[])

def outcomes(s,arm,tasks):
 controls=s.events(arm,'controller.jsonl');states=s.events(arm,'task_state.jsonl');scores=s.events(arm,'scores.jsonl')
 durable={r['payload']['locked_sha256']:r['payload'] for r in controls if r['kind']=='MATH_ANSWER_LOCKED'}
 starts=[r['payload'] for r in controls if r['kind']=='MATH_TASK_STARTED']
 locks={};grades={}
 for r in states:
  p=r['payload'];key=(p.get('sequence'),p.get('task_id'))
  if r['kind']=='ANSWER_LOCKED':
   lock=p['lock'];h=lock['locked_sha256']
   if lock['task_id']!=p['task_id'] or lock['sequence']!=p['sequence']:raise ValueError('task/lock sequence mismatch')
   if fp({k:v for k,v in lock.items() if k!='locked_sha256'})!=h or durable.get(h)!=lock:raise ValueError('invalid durable answer lock')
   if key in locks and locks[key]!=lock:raise ValueError('conflicting task lock')
   locks[key]=lock
  if r['kind']=='PRIVATE_SCORED':
   if key in grades and grades[key]!=p['verdict']:raise ValueError('conflicting private outcome')
   grades[key]=p['verdict']
 result={}
 for seq,t in enumerate(tasks,1):
  key=(seq,t['task_id']);lock=locks.get(key);g=grades.get(key)
  if lock is None or g is None:result[key]=dict(status='INFRASTRUCTURE_MISSING',correct=None);continue
  if g['locked_sha256']!=lock['locked_sha256'] or g['task_id']!=t['task_id']:raise ValueError('score/lock identity mismatch')
  if not any(r['kind']=='MATH_PRIVATE_SCORE' and r['payload']==g for r in scores):raise ValueError('private score receipt missing')
  task_starts=[r for r in starts if r['task_id']==t['task_id']]
  if not task_starts or any(r['problem_sha256']!=fp(t['problem']) for r in task_starts):raise ValueError('paired problem mismatch')
  status=g['status']
  if status in CONFIRMED:
   if g.get('scorer_version')!='math-stream-strict-v1' or g.get('correct') is not (status=='CONFIRMED_CORRECT'):raise ValueError('inconsistent/untrusted confirmed score')
   applied=bool(lock['operator_events'] and lock['operator_events'][-1].get('status')=='APPLIED')
   if not applied and (not lock['responses'] or lock['responses'][-1].get('finish_reason')!='stop'):raise ValueError('truncated response cannot be confirmed mathematical outcome')
  policy=dict(task_starts[0]['policy']);policy.pop('operators_enabled',None)
  correct=True if status=='CONFIRMED_CORRECT' else False if status=='CONFIRMED_WRONG' else None
  result[key]=dict(status=status,correct=correct,lock=lock,grade=g,base_policy=policy)
 return result

def pairs(keys,left,right,lineage):
 wins=losses=both=neither=0;groups=collections.defaultdict(list);original_lineages={};unknown=0
 for key in keys:
  a,b=left[key]['correct'],right[key]['correct']
  if a is None or b is None:continue
  wins+=a and not b;losses+=b and not a;both+=a and b;neither+=not a and not b
  identity=lineage.get(key[1],{})
  if identity.get('source_identity_verified') is True and identity.get('source_original_id') not in (None,'','UNKNOWN') and identity.get('lineage_id') not in (None,'','UNKNOWN'):
   oid=identity['source_original_id'];lid=identity['lineage_id']
   if oid in original_lineages and original_lineages[oid]!=lid:raise ValueError('original lineage conflict')
   original_lineages[oid]=lid;groups[oid].append(int(a)-int(b))
  else:unknown+=1
 means=[sum(x)/len(x) for x in groups.values()]
 clusters=collections.defaultdict(list)
 for oid,values in groups.items():clusters[original_lineages[oid]].append(sum(values)/len(values))
 cluster_means=[sum(v)/len(v) for v in clusters.values()];ow=sum(x>0 for x in cluster_means);ol=sum(x<0 for x in cluster_means)
 weights=[len(values)/len(means) for values in clusters.values()]
 effect=sum(means)/len(means) if means else None
 # Independent lineage clusters, bounded differences in [-1, 1].
 radius=math.sqrt(2*math.log(40)*sum(w*w for w in weights)) if weights else None
 interval=dict(method='weighted_lineage_Hoeffding',level=0.95,
  bounds=[max(-1,effect-radius),min(1,effect+radius)] if radius is not None else None,
  status='CONDITIONAL_ON_INDEPENDENT_LINEAGE_CLUSTERS' if weights else 'NOT_EVALUABLE_ZERO_DENOMINATOR')
 return dict(n=wins+losses+both+neither,status='EVALUABLE' if wins+losses+both+neither else 'NOT_EVALUABLE_ZERO_DENOMINATOR',left_only=wins,right_only=losses,both_correct=both,both_wrong=neither,net_correct_tasks=wins-losses,
  original_equal_weighted_difference=effect,original_effect_interval=interval,verified_originals=len(means),identity_unverified_tasks=unknown,
  lineage_clusters=len(clusters),lineage_cluster_sign_test_p=sign_p(ow,ol) if clusters else None,descriptive_task_mcnemar_exact_p=sign_p(wins,losses) if wins+losses+both+neither else None,
  inference_caveat='Repeated variants are not independent; one adaptive stream is exploratory without prospective controls')

def costs(s,arm,protocol,engineering):
 responses={};reserved={};money=0;tool_ms=0;inheritance=False
 for path,rows in s.logs.items():
  if not path.startswith(arm+'/'):continue
  if path.endswith('budget.jsonl'):
   ledger=None;state={}
   for r in rows:
    p=r['payload'];kind=r['kind']
    if kind=='RUN_OPENED':ledger=p['config']['run_id']
    if kind=='RESERVED':
     rid=p['request_id']
     if rid in state and state[rid]['reservation']!=p:raise ValueError('reservation identity conflict')
     state[rid]=dict(reservation=p,status='reserved')
    if kind in ('SETTLED','UNKNOWN','NOT_SENT','NOT_SENT_REOPENED'):
     rid=p['request_id']
     if rid not in state:raise ValueError('settlement without reservation')
     state[rid]['status']={'SETTLED':'settled','UNKNOWN':'unknown','NOT_SENT':'not_sent','NOT_SENT_REOPENED':'reserved'}[kind]
     if kind=='SETTLED':state[rid]['settlement']=p
    if kind.startswith('INHERITED'):inheritance=True
   for rid,value in state.items():
    k=(ledger,rid)
    if k in reserved and reserved[k]!=value:raise ValueError('duplicated ledger mismatch')
    reserved[k]=value
  if Path(path).name not in ('requests.jsonl','provider.jsonl'):continue
  for r in rows:
   if r['kind']!='RAW_RESPONSE':continue
   p=r['payload'];rid=p.get('request_id',p.get('key'))
   if not rid:raise ValueError('unidentified physical request')
   raw=p['response'];key=(arm,rid)
   if key in responses and responses[key]['raw']!=raw:raise ValueError('conflicting response replay')
   channel='validation' if 'gate_client' in path else 'learning' if '/learning/' in path else 'solve_extra' if '/extra' in rid else 'solve_base'
   responses[key]=dict(raw=raw,channel=channel)
 pending=0;model_requests=0;tool_pending_ms=0
 for value in reserved.values():
  r=value['reservation'];settled=value.get('settlement',{})
  if value['status'] not in ('settled','not_sent'):
   pending+=r['cost_upper_microusd'];tool_pending_ms+=r['tool_milliseconds_upper']
  if r['kind']=='model' and value['status']!='not_sent':model_requests+=1
  if value['status']=='settled':
   money+=settled.get('cost_microusd',0);tool_ms+=settled.get('tool_milliseconds',0)
 channels={};missing_usage=0;missing_price=0
 rates=protocol.get('prices_usd_per_million') or {}
 for item in responses.values():
  raw=item['raw'];u=raw.get('usage',{});i=u.get('prompt_tokens',u.get('input_tokens'));o=u.get('completion_tokens',u.get('output_tokens'))
  row=channels.setdefault(item['channel'],dict(responses=0,input_tokens=0,output_tokens=0,reasoning_tokens=0,estimate=Decimal(0),incomplete_deliveries=0,unpriced_responses=0))
  row['responses']+=1
  finish=raw.get('choices',[{}])[0].get('finish_reason') if len(raw.get('choices',[]))==1 else None
  row['incomplete_deliveries']+=finish not in ('stop',)
  if type(i) is not int or type(o) is not int or min(i,o)<0:missing_usage+=1;row['unpriced_responses']+=1;continue
  row['input_tokens']+=i;row['output_tokens']+=o
  row['reasoning_tokens']+=u.get('completion_tokens_details',{}).get('reasoning_tokens',0) or 0
  rate=rates.get(item['channel'])
  if rate is None:missing_price+=1;row['unpriced_responses']+=1;continue
  for value in rate.values():
   if isinstance(value,bool) or not math.isfinite(float(value)) or float(value)<0:raise ValueError('invalid frozen price')
  hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',i-hit)
  if type(hit) is not int or type(miss) is not int or hit<0 or miss<0 or hit+miss!=i:raise ValueError('cache usage inconsistent')
  row['estimate']+=(Decimal(miss)*Decimal(str(rate['input_uncached']))+Decimal(hit)*Decimal(str(rate['input_cached']))+Decimal(o)*Decimal(str(rate['output'])))/Decimal(1000000)
 missing_response=max(0,model_requests-len(responses));unbound_response=max(0,len(responses)-model_requests);known=sum(r['estimate'] for r in channels.values())
 for r in channels.values():
  estimate=r.pop('estimate');r['estimated_usd']=float(estimate) if not r['unpriced_responses'] else None
 worker_rate=protocol.get('worker_usd_per_second')
 if worker_rate is not None and (isinstance(worker_rate,bool) or not math.isfinite(float(worker_rate)) or float(worker_rate)<0):raise ValueError('invalid Worker price')
 worker_cost=tool_ms/1000*float(worker_rate) if worker_rate is not None else None
 complete=not(missing_usage or missing_price or missing_response or unbound_response or pending or inheritance)
 return dict(channels=channels,recorded_model_requests=model_requests,observed_responses=len(responses),missing_response_count=missing_response,unbound_response_count=unbound_response,
  missing_usage_count=missing_usage,unpriced_response_count=missing_price,estimated_model_usd=float(known) if complete else None,
  estimated_model_known_subtotal_usd=float(known),worker_seconds=tool_ms/1000,worker_pending_upper_seconds=tool_pending_ms/1000,
  estimated_worker_usd=worker_cost,total_estimated_usd=float(known)+worker_cost if complete and worker_cost is not None else None,
  unknown_or_pending_reserved_microusd=pending,ledger_money_settled_microusd=money,actual_supplier_bill_usd=0 if engineering else None,
  status='COMPLETE_ESTIMATE' if complete and worker_cost is not None else 'NOT_EVALUABLE_COMPLETE_COST',
  inherited_ledger_requires_ancestry=inheritance,caveat='Mock usage is simulated; reasoning tokens already included in output; reservations are never billed cost')

def source_version(a):
 if 'operator_contract' not in a:return a['code_sha256']
 return fp(dict(code_sha256=a['code_sha256'],contract_sha256=fp(a['operator_contract']),generation_protocol=a.get('generation_protocol','LEGACY'),source_evidence_identity=a.get('source_evidence_ids',a['operator_contract']['source_evidence']),source_original_ids=a.get('source_original_ids',[])))

def frozen_source_valid(s,a):
 if 'code' in a:return sha(a['code'].encode())==a['code_sha256']
 try:
  for field,digest in [('solver_path','solver_sha256'),('matcher_path','matcher_sha256')]:
   rel=str(Path(a[field]).resolve().relative_to(s.root))
   if rel not in s.bytes or sha(s.bytes[rel])!=a[digest]:return False
  return fp(dict(solver_sha256=a['solver_sha256'],matcher_sha256=a['matcher_sha256'],contract_sha256=fp(a['contract'])))==a['code_sha256']
 except (ValueError,KeyError):return False

def shadow_pairs(snapshot, arm, rows, lineage):
 """Pair the actual locked native answer with the independently scored Shadow answer."""
 events=snapshot.events(arm,'registry.jsonl')
 receipts={r['payload']['execution_id']:r['payload'] for r in events
  if r['kind']=='OPERATOR_VALIDATOR_EXECUTED' and r['payload'].get('stage')=='SHADOW_OBSERVATION'}
 locks={r['payload']['episode_id']:r['payload'] for r in snapshot.logs.get(arm+'/private/contract_shadow/controller.jsonl',[])
  if r['kind']=='MATH_ANSWER_LOCKED'}
 scores=[r['payload'] for r in snapshot.logs.get(arm+'/private/contract_shadow/scores.jsonl',[])
  if r['kind']=='MATH_PRIVATE_SCORE']
 observed={};details=[]
 for event in events:
  if event['kind']!='CONTRACT_SHADOW_EXECUTED':continue
  e=event['payload'];eid=e['execution_id'];key=(e['sequence'],e['task_id'])
  r=receipts.get(eid);baseline=rows.get(key,{});lock=locks.get(eid)
  if r is None or not baseline.get('lock'):continue
  score=r['score']
  if (not lock or lock['task_id']!=key[1] or score.get('task_id')!=key[1]
      or fp({k:v for k,v in lock.items() if k!='locked_sha256'})!=lock['locked_sha256']
      or score.get('locked_sha256')!=lock['locked_sha256'] or lock['operator_events']!=[e['result']]
      or r['binding']!=e['binding'] or r['baseline_result_reference']!=baseline['lock']['locked_sha256']
      or r['result_manifest_sha256']!=fp([e['result'],score]) or score not in scores):
   raise ValueError('unbound Shadow/native pair')
  if any(x.get('status')=='APPLIED' for x in baseline['lock']['operator_events']):continue
  status=score['status']
  if status in CONFIRMED and (score.get('scorer_version')!='math-stream-strict-v1'
      or score.get('correct') is not (status=='CONFIRMED_CORRECT')):
   raise ValueError('invalid Shadow score')
  details.append(dict(sequence=key[0],task_id=key[1],candidate_version=e['binding'],
   native_status=baseline['status'],shadow_status=status,operator_status=e['result']['status']))
  if key in observed:raise ValueError('duplicate Shadow pair')
  observed[key]=dict(correct=score['correct'] if status in CONFIRMED and e['result']['status']=='APPLIED' else None)
 comparison=pairs(observed,observed,rows,lineage)
 return dict(status='EVALUABLE_SHADOW_ONLY' if comparison['n'] else 'NOT_EVALUABLE_NO_CONFIRMED_SHADOW_PAIRS',
  comparison=comparison,records=details)


def reuse(s,arm,rows,generic,lineage,engineering):
 events=s.events(arm,'registry.jsonl');applied=[];independent=[];eligible=[];seen={};excluded=collections.Counter();paired=[]
 for index,r in enumerate(events):
  if r['kind']!='MATH_ROUTER_EXECUTED' or r['payload']['result']['status']!='APPLIED':continue
  p=r['payload'];key=(p['sequence'],p['task_id']);row=rows.get(key)
  if key in seen:
   if seen[key]!=p:raise ValueError('multiple conflicting interventions for one locked task')
   continue
  seen[key]=p
  if not row or row.get('lock') is None or p['result'] not in row['lock']['operator_events']:raise ValueError('unbound intervention')
  applied.append(key)
  if row['correct'] is not None and generic.get(key,{}).get('correct') is not None:paired.append(key)
  reservations=[x['payload'] for x in events[:index] if x['kind']=='V3_TRIAL_RESERVED' and x['payload']['task_id']==key[1] and x['payload']['sequence']==key[0] and x['payload']['code_sha256']==p['code_sha256']]
  versions={x.get('candidate_version') for x in reservations}
  if len(versions)!=1 or None in versions:excluded['AMBIGUOUS_OR_UNBOUND_VERSION']+=1;continue
  version=next(iter(versions));arts=[x['payload'] for x in events[:index] if x['kind']=='MATH_EXPERIMENTAL' and source_version(x['payload']['artifact'])==version and x['payload']['effective_after']<key[0]]
  if not arts:excluded['NO_PRIOR_ADMISSION']+=1;continue
  a=arts[-1]['artifact']
  if not frozen_source_valid(s,a):excluded['SOURCE_NOT_BOUND_TO_FROZEN_BYTES']+=1;continue
  if a.get('operator_contract',{}).get('artifact_kind')!='REUSABLE_CANDIDATE':excluded['INSTANCE_OR_UNDECLARED_OPERATOR']+=1;continue
  if a.get('candidate_version')!=source_version(a):excluded['LEGACY_OR_VERSION_MISMATCH']+=1;continue
  grants=[x['payload'] for x in events[:index] if x['kind']=='V3_TRIAL_AUTHORIZATION' and x['payload'].get('candidate_version')==version and key[1] in x['payload']['task_ids'] and x['payload']['effective_after']<key[0]]
  if not grants:excluded['NO_PRIOR_TASK_AUTHORIZATION']+=1;continue
  grant=grants[-1];uses=sum(x['kind']=='V3_TRIAL_RESERVED' and x['payload'].get('candidate_version')==version for x in events[:index])
  if type(grant.get('max_uses')) is not int or uses>grant['max_uses']:excluded['UNVERIFIED_OR_EXCEEDED_TRIAL_QUOTA']+=1;continue
  if any(x['kind']=='MATH_SUSPENDED' and x['payload'].get('code_sha256')==p['code_sha256'] for x in events[:index]):excluded['PRIOR_SUSPENSION']+=1;continue
  pubs=[x['payload'] for x in events[:index] if x['kind']=='MATH_ROUTER_PUBLICATION' and source_version(x['payload']['artifact'])==version and x['payload'].get('passed') is True]
  if not pubs:excluded['NO_PRIOR_PUBLICATION']+=1;continue
  exposed=False
  for path,data in s.bytes.items():
   if path.startswith(arm+'/') and path.endswith('reviewed_cases.private.json'):
    package=json.loads(data)
    if package.get('candidate_version')==version and any(c['task_id']==key[1] for role in ('Development','Gate') for c in package[role]):exposed=True
  if exposed:excluded['VALIDATION_EXPOSED_TASK']+=1;continue
  identity=lineage.get(key[1],{});sources=[lineage.get(t,{}) for t in a['excluded_task_ids']]
  verified=lambda v:v.get('source_identity_verified') is True and v.get('source_original_id') not in (None,'','UNKNOWN') and v.get('lineage_id') not in (None,'','UNKNOWN')
  if not verified(identity) or not sources or any(not verified(x) for x in sources):excluded['UNVERIFIED_ORIGINAL_OR_LINEAGE']+=1;continue
  if len({v['source_original_id'] for v in sources})<2 or len({v['lineage_id'] for v in sources})<2:excluded['INSUFFICIENT_INDEPENDENT_SOURCES']+=1;continue
  if identity.get('prior_exposure') is not False:excluded['TARGET_PRIOR_EXPOSURE_UNVERIFIED']+=1;continue
  if identity['source_original_id'] in {x['source_original_id'] for x in sources} or identity['lineage_id'] in {x['lineage_id'] for x in sources}:excluded['SOURCE_OR_PARAMETER_LINEAGE_OVERLAP']+=1;continue
  if key[1] in a['excluded_task_ids']:excluded['GENERATION_EXPOSED']+=1;continue
  if row['correct'] is not None:eligible.append(identity['source_original_id'])
  if row['correct'] is True:independent.append(identity['source_original_id'])
 independent_set=set(independent)
 return dict(actual_applied_tasks=len(set(applied)),applied_workflow_pairs_vs_G=pairs(sorted(set(paired)),rows,generic,lineage),
  independent_successes=dict(status='NOT_EVALUABLE_ENGINEERING_MOCK' if engineering else 'EVALUABLE_CONDITIONAL_ON_FROZEN_LINEAGE' if eligible else 'NOT_EVALUABLE_WITHOUT_VERIFIED_INDEPENDENT_SUCCESS',distinct_originals=None if engineering else len(independent_set) if eligible else None,
   successful_uses=None if engineering or not eligible else len(independent),evaluated_uses=None if engineering else len(eligible),
   success_rate=dict(status='NOT_EVALUABLE_ENGINEERING_MOCK',value=None) if engineering else ratio(len(independent),len(eligible))),
  excluded_independence_reasons=dict(excluded),same_checkpoint_causal_pairs=dict(status='NOT_EVALUABLE_NO_FROZEN_CHECKPOINT_COUNTERFACTUAL',count=None),
  independence_assurance='Frozen host lineage labels are inputs, not independently authenticated by this analyzer',
  attribution='Same-task workflow pairs do not identify the isolated causal effect of an operator')

def applicability(s,arm):
 packages=[]
 for path,data in s.bytes.items():
  if path.startswith(arm+'/') and path.endswith('reviewed_cases.private.json'):packages.append(json.loads(data))
 result={}
 for r in s.events(arm,'registry.jsonl'):
  if r['kind']!='V3_VALIDATION':continue
  p=r['payload'];matches=[x for x in packages if x.get('artifact_sha256')==p['code_sha256'] and x.get('candidate_version',x.get('artifact_sha256'))==p.get('candidate_version',p['code_sha256']) and fp(x[p['role']])==p['data_hash']]
  if not matches:continue
  cases=matches[0][p['role']]
  if len(cases)!=len(p['rows']):raise ValueError('semantic review/result count mismatch')
  for c,row in zip(cases,p['rows']):
   if fp(c['problem'])!=row['problem_sha256']:raise ValueError('semantic review problem mismatch')
   key=(p.get('candidate_version',p['code_sha256']),p['role'],c['task_id'])
   value=dict(supported=c['supported'],status=row['observation']['match']['status'],joint=row['combined'],parameter_status=row['applicability'])
   if key in result and result[key]!=value:raise ValueError('conflicting applicability observation')
   result[key]=value
 tables={}
 for (_,role,_),r in result.items():
  t=tables.setdefault(role,collections.Counter());expected=r['supported'];actual=r['status'];t['total']+=1
  if expected is None:t['unverified_labels']+=1;continue
  t['supported' if expected else 'unsupported']+=1
  t['unknown']+=actual=='UNKNOWN';t['error']+=actual=='ERROR'
  t['false_accept']+=expected is False and actual=='MATCH'
  t['false_refuse']+=expected is True and actual=='DECLINE'
  t['true_positive_match']+=expected is True and actual=='MATCH'
  t['joint_correct_accept']+=expected is True and actual=='MATCH' and r['joint']=='CORRECT'
  t['parameter_mapping_error']+=r['parameter_status']=='PARAMETER_MISMATCH'
  t['supported_missed']+=expected is True and actual!='MATCH'
  t['supported_unknown']+=expected is True and actual=='UNKNOWN'
  t['unsupported_unknown']+=expected is False and actual=='UNKNOWN'
 return dict(status='EVALUABLE_CONDITIONAL_ON_FROZEN_HOST_LABELS' if tables else 'NOT_EVALUABLE_NO_BOUND_LABELS',
  label_trust='Reviewer origin/independence not authenticated by this analyzer',by_role={role:dict(t,false_accept_rate=ratio(t['false_accept'],t['unsupported']),false_refuse_rate=ratio(t['false_refuse'],t['supported']),supported_missed_rate=ratio(t['supported_missed'],t['supported']),joint_correct_accept_rate=ratio(t['joint_correct_accept'],t['supported'])) for role,t in tables.items()})

def funnel(s,arm,rows):
 facts=[];candidates={};passed=set()
 for r in s.events(arm,'cumulative/raw.jsonl'):
  if r['kind']!='RAW_EVIDENCE':continue
  p=r['payload'];key=(p['sequence'],p['task']['task_id']);row=rows.get(key,{})
  if p.get('correct') is False and p.get('delivery_status')=='COMPLETE' and row.get('correct') is False and p['locked_sha256']==row['lock']['locked_sha256']:facts.append(p['id'])
 for r in s.events(arm,'registry.jsonl'):
  if r['kind']=='MATH_SHADOW':candidates[source_version(r['payload'])]=r['payload']
  if r['kind']=='OPERATOR_CONTRACT_REVIEW' and r['payload']['stage']=='INDEPENDENT_GATE' and r['payload']['passed']:passed.add(r['payload']['binding'])
 covered={i for v in passed for i in candidates.get(v,{}).get('source_evidence_ids',[]) if i in facts}
 return dict(trusted_failure_events=len(set(facts)),received_candidates=len(candidates),gate_passed_candidate_versions=len(passed),
  trusted_failure_events_contributing_to_passed_gate=len(covered),failure_to_gate_evidence_coverage=ratio(len(covered),len(set(facts))),
  candidate_to_gate=ratio(len(passed & set(candidates)),len(candidates)),caveat='Evidence coverage and candidate conversion are different denominators; Gate is not research benefit')

def diagnostic_learning(s,arm,rows):
 attempts=[r['payload'] for r in s.events(arm,'cumulative/association_attempts.jsonl')
           if r['kind']=='ASSOCIATION_ATTEMPT']
 attempted={eid for r in attempts for eid in r['evidence_ids']}
 linked={eid for r in s.events(arm,'cumulative/clusters.jsonl') if r['kind']=='CLUSTER_VERSION'
         for eid,link in r['payload']['links'].items() if link['relation']!='UNRELATED'}
 queue=s.events(arm,'cumulative/queue.jsonl')
 started={r['payload']['job_id'] for r in queue if r['kind']=='CUMULATIVE_JOB_STARTED'}
 finished={r['payload']['job_id']:r['payload']['result'] for r in queue if r['kind']=='CUMULATIVE_JOB_FINISHED'}
 generated={r['payload'].get('learning_provenance',{}).get('candidate_generation_job_id')
            for r in s.events(arm,'registry.jsonl') if r['kind']=='MATH_SHADOW'} & started
 generated.update(job for job,r in finished.items() if r.get('artifact'))
 reasons=collections.Counter(r.get('status','UNKNOWN') for r in finished.values() if not r.get('artifact'))
 for r in finished.values():
  if r.get('reason') and not r.get('artifact'):reasons['reason: '+str(r['reason'])]+=1
 statuses=collections.Counter(r['status'] for r in rows.values())
 return dict(confirmed_math_failures=statuses['CONFIRMED_WRONG'],
             confirmed_accuracy=ratio(statuses['CONFIRMED_CORRECT'],statuses['CONFIRMED_CORRECT']+statuses['CONFIRMED_WRONG']),
             association_attempts=len(attempts),
             accepted_association_attempts=ratio(sum(r['outcome'].startswith('ACCEPTED') for r in attempts),len(attempts)),
             associated_evidence_rate=ratio(len(attempted & linked),len(attempted)),
             association_outcomes=dict(collections.Counter(r['outcome'] for r in attempts)),
             association_links='MODEL_HYPOTHESES_UNVERIFIED',
             candidate_generation_rate=ratio(len(generated),len(started)),
             candidate_jobs_finished=len(finished),candidate_rejection_reasons=dict(reasons),
             candidate_source_diagnostics=dict(collections.Counter(
                 r.get('status','UNKNOWN') for r in finished.values() if r.get('artifact'))))


def analyze(manifest):
 s=Snapshot(manifest);protocol=s.refs['protocol'];tasks=s.refs['tasks'];lineage=s.refs['lineage']
 if protocol.get('version')!=VERSION or protocol.get('arms')!=list(ARMS) or protocol.get('primary')!='F_minus_G_equal_weighted_original_accuracy_on_common_confirmed_tasks' or protocol.get('statistical_method')!='exact_two_sided_sign_test_on_verified_lineage_clusters':raise ValueError('analysis protocol')
 if len({t['task_id'] for t in tasks})!=len(tasks):raise ValueError('duplicate scheduled task')
 starts=[r['payload'] for r in s.logs.get('stream.jsonl',[]) if r['kind']=='STREAM_FROZEN']
 if len(starts)!=1 or starts[0]['tasks_sha256']!=fp(tasks):raise ValueError('task schedule freeze mismatch')
 plan=starts[0];diagnostic=plan.get('experiment_mode')=='LEARNING_DIAGNOSTIC';mock=any(r['kind']=='STREAM_COMPLETED' and r['payload'].get('paid_api') is False for rows in s.logs.values() for r in rows)
 mock=mock or any(r['payload'].get('origin')=='MOCK' or r['kind']=='MATH_SHADOW' and r['payload'].get('origin')=='MOCK' for rows in s.logs.values() for r in rows)
 mock=mock or any(json.loads(data).get('origin')=='ENGINEERING_FIXTURE' for path,data in s.bytes.items() if path.endswith('reviewed_cases.private.json'))
 mock=mock or any(str(v.get('source_original_id','')).startswith(('MOCK','ENGINEERING')) for v in lineage.values())
 implementation_sha=sha(Path(__file__).read_bytes())
 prospective=plan.get('analysis_protocol_sha256')==fp(protocol) and plan.get('analysis_implementation_sha256')==implementation_sha
 tainted=sum(r['payload'].get('gold_exposed') is True for records in s.logs.values() for r in records)
 rows={a:outcomes(s,a,tasks) for a in ARMS};keys=[(i,t['task_id']) for i,t in enumerate(tasks,1)]
 common=[k for k in keys if all(rows[a][k]['correct'] is not None for a in ARMS)]
 arms={}
 for a in ARMS:
  statuses=collections.Counter(r['status'] for r in rows[a].values());known=sum(r['correct'] is True for r in rows[a].values());unknown=sum(r['correct'] is None for r in rows[a].values())
  arms[a]=dict(status_counts=dict(statuses),confirmed_successes=known,scheduled_tasks=len(tasks),success_sensitivity=dict(lower=known/len(tasks) if tasks else None,upper=(known+unknown)/len(tasks) if tasks else None,unknown_outcomes=unknown),reuse=reuse(s,a,rows[a],rows['G'],lineage,mock),applicability=applicability(s,a),funnel=funnel(s,a,rows[a]),costs=costs(s,a,protocol,mock))
 if diagnostic:
  for a in ARMS:
   if arms[a]['reuse']['actual_applied_tasks'] or arms[a]['funnel']['gate_passed_candidate_versions']:
    raise ValueError('DIAGNOSTIC run contains forbidden Gate or operator intervention')
   arms[a]['diagnostic_learning']=diagnostic_learning(s,a,rows[a])
 for value in arms.values():
  cost=value['costs']['total_estimated_usd'];success=value['confirmed_successes']
  value['cost_per_confirmed_success']=dict(value=cost/success if cost is not None and success else None,status='EVALUABLE_ESTIMATE' if cost is not None and success else 'NOT_EVALUABLE_MISSING_COST_OR_ZERO_SUCCESS')
 comparisons={a:pairs(common,rows['F'],rows[a],lineage) for a in ('G','T','R')}
 policy_mismatches=sum(any(rows[a][k].get('base_policy')!=rows['G'][k].get('base_policy') for a in ARMS) for k in common)
 result=dict(version=VERSION,analysis_implementation_sha256=implementation_sha,snapshot_sha256=sha(s.manifest_bytes),protocol_sha256=fp(protocol),research_scope=('DIAGNOSTIC_ENGINEERING' if mock else 'DIAGNOSTIC') if diagnostic else 'ENGINEERING_ONLY' if mock else 'FROZEN_RECORDS_WITHOUT_ENGINEERING_MARKER',
  analysis_status='TAINTED_NOT_RESEARCH_EVALUABLE' if tainted else 'DIAGNOSTIC' if diagnostic else 'PROSPECTIVE_PLAN_BOUND_TO_RUN' if prospective and not mock else 'EXPLORATORY_POSTHOC_OR_ENGINEERING',recorded_gold_exposure_events=tainted,common_confirmed_tasks=len(common),scheduled_tasks=len(tasks),comparisons_F_minus=comparisons,arms=arms,
  common_tasks_with_base_policy_mismatch=policy_mismatches,
  comparability='NONCOMPARABLE_BASE_POLICIES' if policy_mismatches else 'BASE_POLICIES_MATCH',
  task_outcomes=[dict(sequence=k[0],task_id=k[1],arms={a:rows[a][k]['status'] for a in ARMS}) for k in keys],
  shadow_native_pairs={a:shadow_pairs(s,a,rows[a],lineage) for a in ARMS},
  primary=protocol['primary'],causal_operator_benefit='NOT_ESTABLISHED_BY_WORKFLOW_PAIRS',input_unchanged=True,actual_new_model_requests=0)
 s.verify();return result

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 f=sub.add_parser('freeze');f.add_argument('--run',required=True);f.add_argument('--tasks',required=True);f.add_argument('--lineage',required=True);f.add_argument('--protocol',required=True);f.add_argument('--output',required=True)
 a=sub.add_parser('analyze');a.add_argument('--manifest',required=True);a.add_argument('--output',required=True)
 args=p.parse_args()
 if Path(args.output).exists():raise FileExistsError('choose a new analysis output; existing record retained')
 if args.command=='freeze':freeze(args.run,args.tasks,args.lineage,args.protocol,args.output)
 else:
  result=analyze(args.manifest);root=Path(json.loads(Path(args.manifest).read_text())['root']).resolve();path=external_output(args.output,root)
  private_write(path,json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(dict(status=result['analysis_status'],scope=result['research_scope'],common_confirmed_tasks=result['common_confirmed_tasks'],input_unchanged=True)))
if __name__=='__main__':main()
