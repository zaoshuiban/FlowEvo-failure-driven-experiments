"""New delivery protocol; frozen V4.1 parent, no initial algorithm generation."""
import sys,json,time,collections,random
from pathlib import Path
from run_hard10_algorithm import ROOT,WORKER,IMAGE,save,load,sha,budget,BoundedCompiler,canonical,fingerprint,EvidenceStore,FrozenLinuxBackend
from failure_evo.autonomous_generation import DeepSeekCompilerAdapter
from failure_evo.delivery_reception import receive,VERSION,content_change
from failure_evo.math_execution_v4 import execute_frozen,validate_parameters
from failure_evo.semantic_contract import component_check
from failure_evo.property_validation import adjudicate,bind_validation
from failure_evo.run_health import assert_run_healthy
from run_v42_properties import BASE,PROPERTY,REVIEW,CODE
OUT=ROOT/'runs/flowevo_v42_delivery_20261029_01';OLD=ROOT/'runs/flowevo_v42_20261028';V4=ROOT/'runs/flowevo_v4_20261028'
PROPERTY_SCHEMA={'diagnosis':'nonempty string','replacement_hypothesis':'nonempty string','properties':[{'id':'string','claim':'string','preconditions':'string or list of strings','tests':[{'relation':'oracle_correct OR equal OR different','left':'parameter object','right':'null only for oracle_correct; parameter object required for equal/different'}]}]}
class Adapter(DeepSeekCompilerAdapter):
 protocol='v42-delivery-repair-v1'
 def preflight(self,r):
  self._authorize();self.stage=r['stage'];self.arm=r['arm'];self.receipt=None;self.received_value=None
  inp=r['public_input'];allowed={'problem','schema','failure_evidence','previous_code','diagnostics','analysis','original_response','delivery_diagnostics'}
  if set(inp)-allowed:raise ValueError('public projection violation')
  system=BASE+(PROPERTY+' Exact output structure: '+canonical(PROPERTY_SCHEMA) if self.stage=='properties' else REVIEW if self.stage=='review' else CODE)
  system+=' Do not supply a top-level tests field. Self-tests must be separate data, never module-level execution. Description/applicability are optional documentation; code and mathematical claims are not optional. Never replace an incomplete relation with an inferred meaning.'
  if 'original_response' in inp:system+=' This is one bounded delivery clarification. Preserve code and property content where only packaging is wrong. If mathematical content must change, explicitly state the change in the content itself; the host will register a new version and revalidate. Do not add hidden answers.'
  if self.stage=='compliance':system+=' Change only what is necessary to satisfy the static language restrictions. Do not run self-tests on import. The result is a new model-authored version and will be revalidated.'
  body=dict(model=self.model,messages=[dict(role='system',content=system),dict(role='user',content=canonical(inp))],max_tokens=r['max_tokens'],temperature=.2,thinking={'type':'disabled'},reasoning_effort='none',stream=False,response_format={'type':'json_object'})
  if len(canonical(body).encode())+256>65536:raise ValueError('wire bound')
  return body
 def _normalize_response(self,raw):
  n=super()._normalize_response(raw)
  if n['status']!='completed':return n
  self.received_value=json.loads(n['output'][0]['content'][0]['text']);self.receipt=receive(self.stage,self.received_value)
  self.events.append('DELIVERY_RECEPTION',dict(arm=self.arm,stage=self.stage,raw_value=self.received_value,receipt=self.receipt),time.time())
  if self.receipt['status']=='REJECTED':raise ValueError('RECEPTION_REJECTED:'+canonical(self.receipt['errors']))
  n['output'][0]['content'][0]['text']=canonical(dict(code=canonical(self.receipt['normalized']),description='Host transport envelope; content remains model-authored',applicability='No permission granted'))
  return n

def audit_old():
 rows=[]
 for d in sorted((OLD/'jobs').iterdir()):
  events=EvidenceStore(d/'provider.jsonl').records();raw=next(e['payload']['response'] for e in events if e['kind']=='RAW_RESPONSE');stage=d.name.split('-')[-1]
  try:r=receive(stage,json.loads(raw['choices'][0]['message']['content']))
  except ValueError as e:r=dict(status='REJECTED',errors=[str(e)])
  static=None
  if 'normalized' in r and 'code' in r['normalized']:static=component_check(r['normalized']['code'],'solve')
  rows.append(dict(job=d.name,response_id=raw['id'],raw_sha256=fingerprint(raw),receipt=r,static=static,scope='NEW_PROTOCOL_READ_ONLY_REPLAY_NOT_OLD_SCORE'))
 save(OUT/'historical_reception_replay.json',rows)
 return rows

def freeze():
 if (OUT/'freeze.json').exists():raise RuntimeError('already frozen')
 audit_old()
 a=next(a for a in load(V4/'artifact_manifest.json') if a['slug']=='counting_and_probability-351' and a['arm']=='FC')
 save(OUT/'parent_manifest.json',a);(OUT/'parent.py').write_bytes(Path(a['source_path']).read_bytes());assert sha(OUT/'parent.py')==a['sha256']
 save(OUT/'public_source.json',load(OLD/'public_sources.json')['walk'])
 # Previously exposed confirmation is development-only, never renamed fresh.
 dev=load(OLD/'private/development.json')['walk'];save(OUT/'private/development.json',dev)
 prior={fingerprint(r['parameters']) for r in load(V4/'private/tests.json') if r['family']=='walk'}
 prior|={fingerprint(r['parameters']) for r in load(OLD/'private/confirmation.json') if r['family']=='walk'}
 from v42_oracles import reference
 rng=random.Random(4292026);tests=[];seen=set(prior)
 for i in range(2000):
  steps=[[[1,0],[-1,0],[0,1],[0,-1]],[[2,0],[-1,0],[0,1]],[[0,0],[1,0],[0,1]],[[1,0],[1,0],[-1,0],[0,-1]],[[0,2],[0,-1],[1,0]]][i%5]
  tx,ty=(0,0) if len(tests)<6 else (rng.randint(-5,5),rng.randint(-5,5))
  p=dict(target_x=tx,target_y=ty,max_steps=1+rng.randrange(10),step_set=steps);h=fingerprint(p)
  if h in seen:continue
  expected=reference('walk',p)
  if expected is None:continue
  seen.add(h);tests.append(dict(id='new-confirm-'+str(len(tests)),parameters=p,expected=expected))
  if len(tests)==30:break
 assert len(tests)==30;save(OUT/'private/new_confirmation.json',tests)
 files=[Path(__file__),ROOT/'scripts/v42_oracles.py',ROOT/'scripts/v4_test_data.py',ROOT/'scripts/run_v42_properties.py']+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
 protocol=dict(version=Adapter.protocol,at=time.time(),model='deepseek-flash',parent_sha256=a['sha256'],selection='one existing statically executable erroneous V4.1 random-walk FC; no new initial A/B',arms=['C','B-R'],initial_generation=0,semantic_revisions_per_arm=1,delivery_clarifications_per_stage=1,compliance_repairs_per_arm=1,output_tokens=8192,input_upper=65536,temperature=.2,max_physical_requests=12,tool_inputs_per_development_arm=16,property_spec_limit=8,normalization_version=VERSION,confirmation_count=30,confirmation_role='new parameter confirmation only; not different original tasks',revision_gate='only independent algorithm counterexample or supported execution failure on valid reference-backed parameters; false relation or UNVERIFIED alone never triggers repair',feedback='parameters, candidate output and binary/category only; no reference output or private oracle implementation',safety='unchanged V4 permissions, nonlocal rejected; model compliance repair is new version, no host rewriting',no_auto_promotion=True,authorization='Explicit user request to repair delivery and complete one real property-driven revision experiment; new independent finite run, no initial synthesis',stops=['UNKNOWN','unsettled ledger','Worker infrastructure','source/hash contamination'],source_hashes={str(f.relative_to(ROOT)):sha(f) for f in files},data_hashes={str(f.relative_to(OUT)):sha(f) for f in [OUT/'parent.py',OUT/'parent_manifest.json',OUT/'public_source.json',OUT/'private/development.json',OUT/'private/new_confirmation.json']},worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest())
 save(OUT/'protocol.json',protocol);save(OUT/'freeze.json',dict(hash=fingerprint(protocol)))
 for rel in protocol['source_hashes']:
  d=OUT/'frozen_source'/rel;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes((ROOT/rel).read_bytes())
 save(OUT/'history_hashes.json',{str(f.relative_to(ROOT)):sha(f) for root in [OLD,V4,ROOT/'runs/hard140_algorithm_20261028_01'] for f in root.rglob('*') if f.is_file()})
 print('FROZEN',fingerprint(protocol))

def verify():
 p=load(OUT/'protocol.json');assert fingerprint(p)==load(OUT/'freeze.json')['hash']
 for rel,h in p['source_hashes'].items():assert sha(ROOT/rel)==h,rel
 for rel,h in p['data_hashes'].items():assert sha(OUT/rel)==h,rel
 return p

def one_call(arm,stage,inp,attempt=0):
 p=verify();key=f'{arm}-{stage}-{attempt}';d=OUT/'jobs'/key
 if (d/'consumed.json').exists():raise RuntimeError('request consumed')
 # Check all prior phase ledgers before dispatching another request.
 from failure_evo.persistent_budget import PersistentBudget
 for path in OUT.glob('jobs/*/budget.jsonl'):
  obj=PersistentBudget.__new__(PersistentBudget);obj.path=path
  with obj._locked() as rr:
   state,_=obj._state(rr)
   if any(v['status']!='settled' for v in state.values()):raise RuntimeError('UNSETTLED_GLOBAL_LEDGER')
 b=budget(d/'budget.jsonl',OUT.name+':'+key,fingerprint(p),1,200000)
 auth=dict(run_id=b.config['run_id'],protocol_hash=fingerprint(p),model=p['model'],protocol=Adapter.protocol,max_cost_microusd=200000,paid_api_authorized=True)
 a=Adapter(d/'provider.jsonl',b,model=p['model'],authorization=auth,max_wire_input_upper=65536);c=BoundedCompiler(a,b,d/'compiler.jsonl',p['model'],max_input_upper=65536,max_output_upper=8192)
 save(d/'spec.json',dict(interface='solve(parameters)'));job=dict(stream_id=b.config['run_id'],family_id='one',stage=stage,arm=arm,public_input=inp);job['specification']=c.import_specification(job,d/'spec.json',time.time());save(d/'consumed.json',dict(at=time.time(),authorization=auth))
 try:
  r=c.request(job,'candidate',0,time.time(),8192);save(d/'response.json',r);accepted=json.loads(r['code'])
 except ValueError as e:
  assert_run_healthy(budgets=[b],providers=[a]);save(d/'rejection.json',dict(reason=str(e)));accepted=None
 save(d/'reception.json',dict(raw_value=a.received_value,receipt=a.receipt))
 return accepted,a.received_value,a.receipt

def deliver(arm,stage,inp):
 value,raw,receipt=one_call(arm,stage,inp)
 needs=value is None or (stage=='properties' and receipt and receipt['test_audit'] and not any(t['status']=='EVALUABLE_SPEC' for t in receipt['test_audit']))
 if not needs:return value
 # One shared reception clarification. Content changes explicitly create a new version.
 newer,newraw,newreceipt=one_call(arm,stage,dict(inp,original_response=raw,delivery_diagnostics=receipt or {'reason':'incomplete response'}),1)
 changed=newer is not None and (raw is None or content_change(raw,newer,stage))
 save(OUT/'repairs'/(arm+'-'+stage+'.json'),dict(before_sha256=fingerprint(raw),after_sha256=fingerprint(newer),content_changed=changed,classification='NEW_CONTENT_VERSION_REVALIDATED' if changed else 'FORMAT_ONLY_CONTENT_PRESERVED',receipt=newreceipt))
 return newer

def make_artifact(arm,value,parent):
 d=OUT/'artifacts'/arm
 if value is None:r=dict(status='DELIVERY_FAILURE',parent=parent)
 else:
  d.mkdir(parents=True,exist_ok=True);(d/'solve.py').write_text(value['code']);r=dict(status='STATIC_VALID' if component_check(value['code'],'solve')['passed'] else 'STATIC_REJECTED',sha256=sha(d/'solve.py'),path=str(d/'solve.py'),review=component_check(value['code'],'solve'),parent=parent)
 save(d/'manifest.json',r);return r

def execute(a,p):
 if a['status']!='STATIC_VALID':return dict(status=a['status'])
 schema=load(OUT/'public_source.json')['schema'];check=validate_parameters(p,schema)
 if check['status']!='PARAMETERS_VALID':return dict(status='PARAMETER_SCHEMA_ERROR',detail=check)
 start=time.monotonic();r=execute_frozen(Path(a['path']),a['sha256'],p,FrozenLinuxBackend(image=IMAGE,worker_script=WORKER));r['host_wall_seconds']=time.monotonic()-start
 EvidenceStore(OUT/'worker.jsonl').append('EXECUTED',dict(code_sha256=a['sha256'],input_sha256=fingerprint(p),result=r,gold_exposed=False),time.time());return r

def assess(a,proposal):
 from v42_oracles import reference
 rec=[];used=0
 for prop in proposal['properties']:
  for t in prop['tests']:
   valid=isinstance(t,dict) and set(t)=={'relation','left','right'} and t['relation'] in ('oracle_correct','equal','different') and isinstance(t['left'],dict) and (t['right'] is None or isinstance(t['right'],dict)) and (t['relation']=='oracle_correct' or isinstance(t['right'],dict))
   if not valid:rec.append(dict(property_id=prop['id'],test=t,verdict=dict(status='UNVERIFIED',reason='SEMANTICALLY_INCOMPLETE_TEST'),executions=[]));continue
   ps=[t['left']]+([t['right']] if t['right'] is not None else [])
   refs=[reference('walk',p) for p in ps]
   if any(x is None for x in refs):verdict=dict(status='UNVERIFIED',reason='NO_TRUSTED_REFERENCE');ex=[]
   else:
    if used+len(ps)>16:raise RuntimeError('tool quota')
    ex=[execute(a,p) for p in ps];used+=len(ps);verdict=adjudicate(t['relation'],refs,ex)
   rec.append(dict(property_id=prop['id'],test=t,verdict=verdict,executions=ex,claim_verification='ONLY_INSTANTIATED_RELATION; PROSE_NOT_UNIVERSALLY_PROVEN'))
 return bind_validation(a['sha256'],proposal,rec,'DEVELOPMENT')

def run():
 verify()
 if (OUT/'STARTED.json').exists():raise RuntimeError('consumed run; no resend')
 save(OUT/'STARTED.json',dict(at=time.time()));parent=load(OUT/'parent_manifest.json');a=dict(status='STATIC_VALID',sha256=parent['sha256'],path=str(OUT/'parent.py'));source=load(OUT/'public_source.json');base=dict(source,previous_code=(OUT/'parent.py').read_text());versions={'parent':a}
 try:
  for arm in ['C','B-R']:
   if arm=='C':
    proposal=deliver(arm,'properties',base)
    if proposal is None:versions[arm]=dict(status='NOT_GENERATED',reason='proposal unavailable');continue
    receipt=assess(a,proposal);save(OUT/'properties.json',dict(proposal=proposal,receipt=receipt))
    analysis=proposal
   else:
    dev=load(OUT/'private/development.json');ordinary=dict(diagnosis='Host ordinary test feedback',replacement_hypothesis='No property supplied',properties=[dict(id='ordinary',claim='Reference agreement',preconditions='Valid reference-supported inputs',tests=[dict(relation='oracle_correct',left=p,right=None) for p in dev])]);receipt=assess(a,ordinary);save(OUT/'ordinary_feedback.json',receipt)
    analysis=deliver(arm,'review',dict(base,diagnostics=receipt))
   valid_counter=any(r['verdict']['status']=='ALGORITHM_COUNTEREXAMPLE' for r in receipt['records'])
   save(OUT/(arm+'_gate.json'),dict(counterexample_established=valid_counter,source_sha256=a['sha256'],reference_answers_sent=False))
   if not valid_counter or analysis is None:versions[arm]=dict(status='NOT_REVISED',reason='no valid algorithm counterexample or unavailable analysis',parent=a['sha256']);continue
   value=deliver(arm,'revision',dict(base,analysis=analysis,diagnostics=receipt));child=make_artifact(arm,value,a['sha256'])
   if child['status']=='STATIC_REJECTED':
    fixed=deliver(arm,'compliance',dict(source,previous_code=value['code'],diagnostics=child['review']));child=make_artifact(arm+'-compliance',fixed,child['sha256']);child['initial_revision']=str(OUT/'artifacts'/arm/'manifest.json')
   versions[arm]=child;save(OUT/'progress.json',versions);print('REVISED',arm,child['status'],flush=True)
  save(OUT/'candidate_freeze.json',dict(at=time.time(),versions=versions));save(OUT/'GENERATION_COMPLETE.json',dict(at=time.time()))
 except BaseException as e:save(OUT/'STOP.json',dict(reason=str(e),at=time.time(),versions=versions));raise

def evaluate():
 verify()
 if not (OUT/'GENERATION_COMPLETE.json').exists() or (OUT/'EVALUATION_STARTED.json').exists():raise RuntimeError('evaluation gate')
 save(OUT/'EVALUATION_STARTED.json',dict(at=time.time()));versions=load(OUT/'candidate_freeze.json')['versions'];dev=load(OUT/'private/development.json');fresh=load(OUT/'private/new_confirmation.json');source=load(OUT/'parent_manifest.json')['analysis']['source_parameters'];results=[]
 from v42_oracles import reference
 for arm,a in versions.items():
  if a['status'] not in ('STATIC_VALID','STATIC_REJECTED','DELIVERY_FAILURE'):continue
  cases=[dict(id='source',parameters=source,role='source')]+[dict(id='dev-'+str(i),parameters=p,role='development_regression') for i,p in enumerate(dev)]+[dict(id=x['id'],parameters=x['parameters'],role='new_parameter_confirmation') for x in fresh]
  for c in cases:
   r=execute(a,c['parameters']);expected=reference('walk',c['parameters']);status=r['status']
   if status=='EXECUTED_UNSCORED':status='UNVERIFIED' if expected is None else 'MATHEMATICAL_CORRECT' if r['raw']['value']==expected else 'MATHEMATICAL_WRONG'
   results.append(dict(arm=arm,case_id=c['id'],role=c['role'],status=status,raw=r,source_sha256=a.get('sha256')))
  if (OUT/'properties.json').exists() and a['status']=='STATIC_VALID':save(OUT/'property_rechecks'/(arm+'.json'),assess(a,load(OUT/'properties.json')['proposal']))
  save(OUT/'evaluation_progress.json',results);print('EVALUATED',arm,flush=True)
 save(OUT/'evaluation_results.json',results);save(OUT/'COMPLETE.json',dict(at=time.time()))
if __name__=='__main__':globals()[sys.argv[1]]()
