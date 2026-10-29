"""Versioned GPT-produced semantic contracts and isolated component execution."""
import ast,hashlib,json,time
from pathlib import Path
from .contracts import canonical,fingerprint
from .math_operators import validate_math_source
from .autonomous_mvp import FrozenLinuxBackend
FIELDS=('operator_id','supported_problem_structure','requested_quantity','required_constraints','forbidden_constraints','parameter_schema','parameter_extraction_rules','supported_numeric_domain','resource_boundaries','semantic_ambiguity_policy','expected_refusal_conditions')
SCHEMA=dict(type='object',additionalProperties=False,required=list(FIELDS),properties={k:dict(type='string') for k in FIELDS})
def parse_contract(v):
 if not isinstance(v,dict) or set(v)!=set(FIELDS) or any(not isinstance(x,str) or not x.strip() for x in v.values()):raise ValueError('semantic contract exact strings')
 schema=json.loads(v['parameter_schema'])
 if schema.get('type')!='object' or schema.get('additionalProperties') is not False:raise ValueError('closed object parameter schema required')
 import jsonschema
 jsonschema.Draft202012Validator.check_schema(schema)
 # No external reference resolution, network or unbounded schema recursion.
 def walk(x,depth=0):
  if depth>12:raise ValueError('schema nesting bound')
  if isinstance(x,dict):
   allowed={'type','properties','required','additionalProperties','items','enum','const','minimum','maximum','minItems','maxItems','minLength','maxLength','description','title','uniqueItems'}
   if set(x)-allowed:raise ValueError('unsupported schema capability')
   for key,value in x.items():
    if key=='properties':
     if not isinstance(value,dict):raise ValueError('schema properties')
     for child in value.values():walk(child,depth+1)
    elif key=='items':walk(value,depth+1)
  elif isinstance(x,list):
   for y in x:walk(y,depth+1)
 walk(schema)
 if len(canonical(v))>24000:raise ValueError('contract bound')
 return v

def component_check(code,entry):
 if entry not in ('match','solve'):raise ValueError('component entry')
 try:t=ast.parse(code)
 except SyntaxError:return dict(passed=False,errors=['SYNTAX'])
 funcs=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==entry]
 if len(funcs)!=1 or any(isinstance(n,ast.FunctionDef) and n.name=='math_operator' for n in t.body):return dict(passed=False,errors=['ENTRY'])
 a=funcs[0].args
 if len(a.args)!=1 or a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg:return dict(passed=False,errors=['SIGNATURE'])
 # Reuse existing permission validator without imposing the old scalar return contract on match.
 return validate_math_source(code+"\ndef math_operator(context):\n    return {'status':'DECLINED','reason':'static-adapter-only'}\n")

def artifact(directory,solver,matcher,contract,*,provenance,parent=None):
 parse_contract(contract)
 for code,name in ((solver,'solve'),(matcher,'match')):
  c=component_check(code,name)
  if not c['passed']:raise ValueError(name+':'+','.join(c['errors']))
 d=Path(directory);d.mkdir(parents=True,exist_ok=True)
 sh=hashlib.sha256(solver.encode()).hexdigest();mh=hashlib.sha256(matcher.encode()).hexdigest()
 identity=dict(solver_sha256=sh,matcher_sha256=mh,contract_sha256=fingerprint(contract))
 joint=fingerprint(identity)
 for name,code in [('solve',solver),('match',matcher)]:
  p=d/(joint+'.'+name+'.py')
  if p.exists() and p.read_text()!=code:raise ValueError('immutable artifact')
  p.write_text(code)
 return dict(**identity,code_sha256=joint,operator_id=joint[:16],solver_path=str((d/(joint+'.solve.py')).resolve()),matcher_path=str((d/(joint+'.match.py')).resolve()),contract=contract,origin=provenance['origin'],provenance=provenance,parent=parent,excluded_task_ids=provenance.get('excluded_task_ids',[]),contract_version='math-v3-split-v1')

class SplitRunner:
 def __init__(self,backend,journal):
  if not isinstance(backend,FrozenLinuxBackend):raise TypeError('real Linux backend required')
  from .evidence import EvidenceStore
  self.backend=backend;self.events=EvidenceStore(journal)
 def component(self,a,component,value):
  from .evidence import EvidenceStore
  path=Path(a['matcher_path'] if component=='match' else a['solver_path']);digest=a['matcher_sha256' if component=='match' else 'solver_sha256']
  if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise PermissionError('component changed')
  identity={k:a[k] for k in ('solver_sha256','matcher_sha256','contract_sha256')}
  if fingerprint(a['contract'])!=a['contract_sha256'] or fingerprint(identity)!=a['code_sha256']:raise PermissionError('joint artifact changed')
  if not component_check(path.read_text(),component)['passed']:raise PermissionError('static rejection')
  request=dict(mode='function',function=component,args=[value],timeout=2)
  start=time.monotonic()
  with self.backend(path) as worker:raw=worker.call(request)
  elapsed=time.monotonic()-start
  if raw.get('status') in ('EVALUATOR_ERROR','WORKER_ERROR'):raise RuntimeError('Worker infrastructure')
  row=dict(component=component,code_sha256=a['code_sha256'],component_sha256=digest,input_sha256=fingerprint(value),raw=raw,seconds=elapsed,gold_exposed=False)
  self.events.append('V3_COMPONENT_EXECUTED',row,time.time())
  return raw
 def match(self,a,problem):
  parse_contract(a['contract'])
  raw=self.component(a,'match',problem);v=raw.get('value')
  if len(canonical(v))>16384:return dict(status='ERROR',reason='MATCH_OUTPUT_BOUND')
  if raw.get('status')!='OK' or not isinstance(v,dict) or set(v)!={'status','parameters','reason','assumption_quotes','requested_quantity'}:return dict(status='ERROR',reason='MATCH_CONTRACT')
  if v['status'] not in ('MATCH','DECLINE','UNKNOWN') or not isinstance(v['parameters'],dict) or not isinstance(v['reason'],str) or not isinstance(v['assumption_quotes'],list):return dict(status='ERROR',reason='MATCH_CONTRACT')
  if v['status']=='MATCH':
   import jsonschema
   try:jsonschema.validate(v['parameters'],json.loads(a['contract']['parameter_schema']))
   except (jsonschema.ValidationError,jsonschema.SchemaError):return dict(status='UNKNOWN',reason='PARAMETERS_UNVERIFIED')
   if v['requested_quantity']!=a['contract']['requested_quantity']:return dict(status='UNKNOWN',reason='QUANTITY_MISMATCH')
   if not v['assumption_quotes'] or any(not isinstance(q,str) or not q or q not in problem for q in v['assumption_quotes']):return dict(status='UNKNOWN',reason='ASSUMPTION_QUOTES_UNBOUND')
  return v
 def solve(self,a,parameters):
  parse_contract(a['contract'])
  import jsonschema
  try:jsonschema.validate(parameters,json.loads(a['contract']['parameter_schema']))
  except jsonschema.ValidationError:return dict(status='ERROR',reason='PARAMETERS')
  raw=self.component(a,'solve',parameters)
  if raw.get('status')!='OK' or not isinstance(raw.get('value'),str) or not raw['value'].strip() or len(raw['value'])>4096:return dict(status='ERROR',reason='SOLVE_CONTRACT')
  return dict(status='APPLIED',answer=raw['value'])
 def run(self,a,task):
  start=time.monotonic();m=self.match(a,task.problem)
  result=self.solve(a,m['parameters']) if m['status']=='MATCH' else dict(status='ERROR' if m['status']=='ERROR' else 'DECLINED',reason=m.get('reason',m['status']))
  return dict(result,match=m,code_sha256=a['code_sha256'],operator_id=a['operator_id'],seconds=time.monotonic()-start,gold_exposed=False)
