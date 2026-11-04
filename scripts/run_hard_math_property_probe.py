"""Three existing official Level-5 sources, bounded discovery/repair exploration."""
import sys,json,time,random,math,shutil,urllib.request,collections
from pathlib import Path
from fractions import Fraction
import run_v42_discovery_repair as core
from run_hard10_algorithm import ROOT,WORKER,IMAGE,save,load,sha,fingerprint,canonical,FrozenLinuxBackend
from failure_evo.semantic_contract import component_check
OUT=ROOT/'runs/hard_math_property_probe_20261029_01'
OLD=ROOT/'runs/hard140_algorithm_20261028_01'
SPECS={'score':('number_theory-550','FC'),'digits':('number_theory-420','FC'),'radical':('intermediate_algebra-426','F')}
SCOPES={
'score':'Score s=B+A*c-W*w, 0<=c<=N and 0<=w<=N-c, integer counts. Return smallest achievable s strictly above threshold and <=max_score; if require_unique_correct_count true, exactly one c must produce s. No qualifying score => safe ValueError. Certified tests: N 0..50; B -100..100; A,W 0..10; threshold -200..500; max_score>=threshold and <=600.',
'digits':'Positive integers strictly below upper_bound. Return largest with equal decimal digit sum and binary one-bit count. Certified upper_bound is integer 2..100000.',
'radical':'Evaluate the declared bounded-search interface, not an unrestricted existence theorem: p>q>=1 (<=125), multiplier 1..6, bound 1..60, tolerance in [1e-40,1e-2]. Find minimum a+b+c over positive integer a,b,c<=bound with absolute radical-expression difference strictly below tolerance; if none, safe ValueError. Inputs outside this independent-certification range are UNVERIFIED, not a mathematical failure. Exact original-task correctness is reported separately.'}

def oracle(kind,p):
 try:
  if kind=='score':
   keys=['total_problems','base_score','correct_coefficient','wrong_coefficient','threshold','max_score'];N,B,A,W,T,M=[p[k] for k in keys];req=p['require_unique_correct_count']
   if set(p)!=set(keys+['require_unique_correct_count']) or any(type(x)!=int for x in [N,B,A,W,T,M]) or type(req)!=bool or not (0<=N<=50 and abs(B)<=100 and 0<=A<=10 and 0<=W<=10 and -200<=T<=500 and T<=M<=600):return None
   by={}
   for c in range(N+1):
    for w in range(N-c+1):by.setdefault(B+A*c-W*w,set()).add(c)
   good=sorted(s for s,cs in by.items() if T<s<=M and (len(cs)==1 or not req));return dict(status='VALUE',value=str(good[0])) if good else dict(status='NO_SOLUTION')
  if kind=='digits':
   n=p['upper_bound']
   if set(p)!={'upper_bound'} or type(n)!=int or not 2<=n<=100000:return None
   hits=[x for x in range(1,n) if sum(map(int,str(x)))==bin(x).count('1')];return dict(status='VALUE',value=str(max(hits)))
  keys={'p','q','multiplier','bound','tolerance'}
  if set(p)!=keys:return None
  a,b,m,n=[p[k] for k in ['p','q','multiplier','bound']];tol=p['tolerance']
  if any(type(x)!=int for x in [a,b,m,n]) or type(tol) not in (float,int) or not (1<=b<a<=125 and 1<=m<=6 and 1<=n<=60 and 1e-40<=tol<=.01):return None
  # Host-only interval arithmetic, exact integer roots at scale 10**60.
  # No candidate code, model answer, or numerical tolerance heuristic is used as reference.
  import sympy as s
  scale=10**60
  def cube(v):
   lo,exact=s.integer_nthroot(v*scale**3,3);return int(lo),int(lo)+(not exact)
  ap,au=cube(a);bp,bu=cube(b);lo=math.isqrt((ap-bu)*scale);z=(au-bp)*scale;hi=math.isqrt(z);hi+=hi*hi<z;tl,tu=m*lo,m*hi
  roots=[(0,0)]+[cube(i) for i in range(1,n+1)];threshold=Fraction(str(tol))*scale;best=None;uncertain=False
  for i in range(1,n+1):
   for j in range(i,n+1):
    for k in range(1,n+1):
     low=roots[i][0]+roots[j][0]-roots[k][1]-tu;high=roots[i][1]+roots[j][1]-roots[k][0]-tl
     mx=max(abs(low),abs(high));mn=0 if low<=0<=high else min(abs(low),abs(high))
     if mx<threshold:best=min(best,i+j+k) if best is not None else i+j+k
     elif mn<threshold:uncertain=True
  if uncertain:return None
  return dict(status='VALUE',value=str(best)) if best is not None else dict(status='NO_SOLUTION')
 except (ValueError,TypeError,KeyError,OverflowError):return None

def classify(ref,ex):
 if ref is None:return 'UNVERIFIED'
 if ref['status']=='NO_SOLUTION':
  raw=ex.get('raw',{});txt=canonical(raw)
  return 'CORRECT_REJECTION' if ex['status']=='RUNTIME_ERROR' and 'ValueError' in txt else 'WRONG_ACCEPT' if ex['status']=='EXECUTED_UNSCORED' else ex['status']
 if ex['status']=='EXECUTED_UNSCORED':return 'CORRECT' if ex['raw']['value']==ref['value'] else 'WRONG'
 return ex['status']

def verify():
 p=load(OUT/'protocol.json');assert fingerprint(p)==load(OUT/'freeze.json')['sha256']
 for rel,h in p['source_hashes'].items():assert sha(ROOT/rel)==h,rel
 for rel,h in p['data_hashes'].items():assert sha(OUT/rel)==h,rel
 return p

def public(kind,a):return dict(problem=load(OUT/'sources.json')[kind]['problem'],schema=a['schema'],scope=SCOPES[kind],previous_code=Path(a['path']).read_text())

def assay(kind,a,proposal):
 rec=[];used=0;idx=0
 for prop in proposal['properties']:
  for t in prop['tests']:
   idx+=1;row=dict(claim=prop['claim'],property_id=prop['id'],preconditions=prop['preconditions'],test=t)
   valid=isinstance(t,dict) and set(t)=={'relation','left','right'} and t['relation'] in ('oracle_correct','equal','different') and isinstance(t['left'],dict) and (t['right'] is None or isinstance(t['right'],dict)) and (t['relation']=='oracle_correct' or isinstance(t['right'],dict))
   if idx>8:row['status']='NOT_EXECUTED_QUOTA'
   elif not valid:row['status']='UNVERIFIED_SPEC'
   else:
    ps=[t['left']]+([t['right']] if t['right'] is not None else []);refs=[oracle(kind,p) for p in ps]
    if any(x is None for x in refs):row['status']='UNVERIFIED_REFERENCE_OR_DOMAIN'
    elif used+len(ps)>16:row['status']='NOT_EXECUTED_QUOTA'
    else:
     ex=[core.execute(a,p) for p in ps];used+=len(ps);statuses=[classify(r,e) for r,e in zip(refs,ex)];relation_valid=True
     if t['relation']!='oracle_correct':
      relation_valid=all(x['status']=='VALUE' for x in refs)
      if relation_valid:relation_valid=(refs[0]['value']==refs[1]['value'])==(t['relation']=='equal')
     row.update(status='UNVERIFIED_RELATION_NO_VALUE' if t['relation']!='oracle_correct' and any(x['status']!='VALUE' for x in refs) else 'PROPERTY_COUNTEREXAMPLE' if not relation_valid else 'ALGORITHM_COUNTEREXAMPLE' if any(s in ('WRONG','WRONG_ACCEPT','RUNTIME_ERROR','RESOURCE_EXCEEDED','INTERFACE_ERROR') for s in statuses) else 'FINITE_SAMPLE_SUPPORTED',executions=ex,observations=[dict(parameters=p,status=s,actual=e.get('raw',{}).get('value')) for p,s,e in zip(ps,statuses,ex)])
   rec.append(row)
 return dict(source_sha256=a['sha256'],records=rec,worker_input_count=used,property_prose_verified=False)

def configure():
 core.OUT=OUT;core.verify=verify;core.assay=assay;core.public=public;core.Adapter.protocol='hard-math-property-probe-v1'
configure()

def freeze():
 if OUT.exists():raise RuntimeError('new run only')
 OUT.mkdir();tasks={t['task_id']:t for t in load(OLD/'tasks.json')};programs={};sources={};source_labels={x['task_id']:x for x in load(OLD/'private/labels.json')};private_source={}
 for kind,(slug,arm) in SPECS.items():
  tid='hard140-math-train-'+slug;d=OLD/'jobs'/(tid+'-'+arm);a=load(d/'analysis.json');p=OUT/'parents'/(kind+'.py');p.parent.mkdir(exist_ok=True);shutil.copyfile(d/'solve.py',p);assert component_check(p.read_text(),'solve')['passed']
  programs[kind]=dict(status='STATIC_VALID',path=str(p),sha256=sha(p),schema=a['parameter_schema'],source_parameters=a['source_parameters'],origin=str(d/'solve.py'))
  sources[kind]=tasks[tid];private_source[kind]=dict(task_id=tid,gold_answer=source_labels[tid]['gold_answer'],level=source_labels[tid]['level'])
 save(OUT/'programs.json',programs);save(OUT/'sources.json',sources);save(OUT/'private/source_labels.json',private_source)
 rng=random.Random(4292621);sets={}
 for kind in SPECS:
  cand=[]
  for i in range(200):
   if kind=='digits':p=dict(upper_bound=rng.randint(2,99999))
   elif kind=='score':
    N=rng.randint(1,40);B=rng.randint(-20,50);A=rng.randint(0,8);W=i%6;T=rng.randint(-40,120);p=dict(total_problems=N,base_score=B,correct_coefficient=A,wrong_coefficient=W,threshold=T,max_score=500,require_unique_correct_count=i%4!=0)
   else:
    # Generic bounded radical cases; no candidate-output filtering.
    q=rng.randint(1,15);p=dict(p=q+rng.randint(1,30),q=q,multiplier=1+i%4,bound=[8,12,16,20][i%4],tolerance=[1e-8,1e-16,1e-30][i%3])
   if fingerprint(p)==fingerprint(programs[kind]['source_parameters']) or any(fingerprint(p)==fingerprint(x['parameters']) for x in cand):continue
   ref=oracle(kind,p)
   if ref is None:raise RuntimeError('REFERENCE_UNVERIFIED_PRE_FREEZE')
   cand.append(dict(id=kind+'-'+str(len(cand)),parameters=p,reference=ref,role='development_regression' if len(cand)<6 else 'new_parameter_confirmation'))
   if len(cand)==24:break
  assert len(cand)==24;sets[kind]=cand
 save(OUT/'private/cases.json',sets)
 page=urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=20).read();(OUT/'pricing.html').write_bytes(page);assert all(s.encode() in page for s in ['$0.006','$0.3','$1.2'])
 files=[Path(__file__).resolve(),ROOT/'scripts/run_v42_discovery_repair.py',ROOT/'scripts/run_v42_delivery_repair.py',ROOT/'scripts/run_v42_properties.py',ROOT/'scripts/run_hard10_algorithm.py',ROOT/'scripts/run_math_v3_development.py',ROOT/'scripts/test_hard_math_property_probe.py',WORKER]+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
 p=dict(version=core.Adapter.protocol,at=time.time(),model='deepseek-flash',served_model='DeepSeek-V4.1-Flash-1017',selection='Three existing Level5 programs outside closed examples; all chosen before new model outcomes, earliest available executable FC by these subjects, intermediate-algebra F because FC static rejected. Geometry excluded for lack of bounded trusted reference. No initial synthesis.',scope=SCOPES,order=[['score','D'],['score','C'],['digits','C'],['digits','D'],['radical','D'],['radical','C']],repair_order=[['score','C'],['score','D'],['digits','D'],['digits','C'],['radical','C'],['radical','D']],physical_max_calls=36,hard_budget_usd=7.2,per_call_usd=.2,temperature=.2,output_tokens=8192,wire_upper=65536,semantic_revision=1,clarification_per_stage=1,test_specs=8,test_inputs_per_assay=16,stop=['UNKNOWN','hash drift','budget','Worker infrastructure','oracle uncertainty remains unverified'],gold_policy='private references never in model requests; binary and actual candidate outputs only',source_roles='EXPOSED_DEVELOPMENT_LEVEL5',confirmation='18 fresh parameter inputs per family; exclude any proposed overlap without replacement; NOT 54 independent MATH problems',no_initial_generation=True,old_cases_closed=True,authorization='User asks further difficult-MATH exploratory real experiments; bounded new run',source_hashes={str(p.relative_to(ROOT)):sha(p) for p in files},data_hashes={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()},worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest())
 save(OUT/'protocol.json',p);save(OUT/'freeze.json',dict(sha256=fingerprint(p)))
 for rel in p['source_hashes']:
  q=OUT/'frozen_source'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,q)
 history=[OLD,ROOT/'runs/flowevo_v42_discovery_repair_20261029_01',ROOT/'runs/flowevo_v42_delivery_20261029_02']
 save(OUT/'history_hashes.json',{str(p.relative_to(ROOT)):sha(p) for d in history for p in d.rglob('*') if p.is_file()})
 print('FROZEN',fingerprint(p),flush=True)

def preflight():
 verify();programs=load(OUT/'programs.json');rows=[]
 for kind,a in programs.items():
  for x in load(OUT/'private/cases.json')[kind][:2]:
   ex=core.execute(a,x['parameters']);rows.append(dict(kind=kind,status=classify(x['reference'],ex),raw=ex))
 save(OUT/'preflight.json',dict(worker_live=True,results=rows,no_model_api=True));print('PREFLIGHT',[(x['kind'],x['status']) for x in rows],flush=True)

def run():
 p=verify();assert (OUT/'preflight.json').exists();assert not (OUT/'STARTED.json').exists();save(OUT/'STARTED.json',dict(at=time.time()));pr=load(OUT/'programs.json');discovery={};versions={k:{'parent':a} for k,a in pr.items()}
 try:
  for kind,arm in p['order']:
   v=core.deliver(kind,arm,'discover','properties',public(kind,pr[kind]));receipt=assay(kind,pr[kind],v) if v else None;discovery[kind+'-'+arm]=dict(proposal=v,receipt=receipt);save(OUT/'discovery.json',discovery);print('DISCOVERED',kind,arm,collections.Counter(x['status'] for x in receipt['records']) if receipt else 'DELIVERY_FAILURE',flush=True)
  common={}
  for kind in pr:
   found={}
   for arm in ['D','C']:
    rec=discovery[kind+'-'+arm]['receipt']
    for row in rec['records'] if rec else []:
     for o in row.get('observations',[]):
      if o['status'] in ('WRONG','WRONG_ACCEPT','RUNTIME_ERROR','RESOURCE_EXCEEDED','INTERFACE_ERROR'):found[fingerprint(o['parameters'])]=o
   common[kind]=[found[k] for k in sorted(found)]
  save(OUT/'shared_counterexamples.json',common)
  for kind,arm in p['repair_order']:
   if not common[kind]:versions[kind][arm]=dict(status='NOT_REVISED_NO_COUNTEREXAMPLE');continue
   base=dict(public(kind,pr[kind]),diagnostics=common[kind]);plan=core.deliver(kind,arm,'repair_plan','properties',base)
   if plan is None:versions[kind][arm]=dict(status='NO_PLAN');continue
   tests=assay(kind,pr[kind],plan);save(OUT/'repair_plans'/f'{kind}-{arm}.json',dict(proposal=plan,receipt=tests,common_feedback_sha256=fingerprint(common[kind])))
   v=core.deliver(kind,arm,'repair','revision',dict(base,analysis=plan,diagnostics=dict(common_counterexamples=common[kind],own_plan_tests=tests)))
   versions[kind][arm]=core.make_artifact(kind,arm,v,pr[kind]);save(OUT/'progress.json',versions);print('REVISED',kind,arm,versions[kind][arm]['status'],flush=True)
  save(OUT/'candidate_freeze.json',dict(at=time.time(),versions=versions));save(OUT/'GENERATION_COMPLETE.json',dict(at=time.time()))
 except BaseException as e:save(OUT/'STOP.json',dict(reason=str(e),at=time.time()));raise

def evaluate():
 verify();assert (OUT/'GENERATION_COMPLETE.json').exists();assert not (OUT/'EVALUATION_STARTED.json').exists();save(OUT/'EVALUATION_STARTED.json',dict(at=time.time()));vs=load(OUT/'candidate_freeze.json')['versions'];data=load(OUT/'private/cases.json');common=load(OUT/'shared_counterexamples.json');seen={k:set() for k in SPECS}
 for key,v in load(OUT/'discovery.json').items():
  kind=key.rsplit('-',1)[0]
  for row in v['receipt']['records'] if v['receipt'] else []:
   t=row['test']
   if isinstance(t,dict):
    for k in ['left','right']:
     if isinstance(t.get(k),dict):seen[kind].add(fingerprint(t[k]))
 for f in (OUT/'repair_plans').glob('*.json'):
  kind=f.stem.rsplit('-',1)[0]
  for row in load(f)['receipt']['records']:
   for k in ['left','right']:
    if isinstance(row['test'].get(k),dict):seen[kind].add(fingerprint(row['test'][k]))
 rows=[];source=[]
 from code_math.private_math_scoring import normalized
 labels=load(OUT/'private/source_labels.json')
 for kind,arms in vs.items():
  for arm,a in arms.items():
   if a['status']!='STATIC_VALID':continue
   cases=data[kind]+[dict(id='counter-'+str(i),parameters=x['parameters'],reference=oracle(kind,x['parameters']),role='shared_counterexample') for i,x in enumerate(common[kind])]
   for x in cases:
    ex=core.execute(a,x['parameters']);role='exposed_overlap' if x['role']=='new_parameter_confirmation' and fingerprint(x['parameters']) in seen[kind] else x['role'];rows.append(dict(kind=kind,arm=arm,id=x['id'],role=role,status=classify(x['reference'],ex),reference_status=x['reference']['status'],raw=ex))
   original=load(OUT/'programs.json')[kind]['source_parameters'];ex=core.execute(a,original);ref=labels[kind]['gold_answer'];value=ex.get('raw',{}).get('value');st='SOURCE_CORRECT' if ex['status']=='EXECUTED_UNSCORED' and normalized(value)==normalized(ref) else 'SOURCE_WRONG' if ex['status']=='EXECUTED_UNSCORED' else ex['status'];source.append(dict(kind=kind,arm=arm,status=st,raw=ex));save(OUT/'evaluation_progress.json',rows);print('EVALUATED',kind,arm,flush=True)
 save(OUT/'evaluation.json',rows);save(OUT/'source_results.json',source);old=load(OUT/'history_hashes.json');changed=[p for p,h in old.items() if sha(ROOT/p)!=h];assert not changed;save(OUT/'COMPLETE.json',dict(at=time.time(),historical_files=len(old),changed=changed))
if __name__=='__main__':globals()[sys.argv[1]]()
