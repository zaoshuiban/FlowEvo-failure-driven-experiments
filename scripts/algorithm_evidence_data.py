"""Private scoring preparation only. Never sent to synthesis model."""
import ast,json,random,itertools
from fractions import Fraction
from functools import lru_cache
from run_math_v3_development import ROOT,DATA,save,sha
from failure_evo.contracts import fingerprint
REF=DATA/'private/original_sources/scripts/baseline_failure_mechanisms_v2.py'
def references():
 tree=ast.parse(REF.read_text());ns=dict(Fraction=Fraction,lru_cache=lru_cache)
 funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['_is_prime','_parenthesized_values']]
 exec(compile(ast.Module(body=funcs,type_ignores=[]),str(REF),'exec'),ns);return ns

def oracle(family,p,refs):
 if family=='D':
  digits=p['digits'];length=p['max_length'];first=set()
  for n in range(1,length+1):
   for arr in itertools.permutations(digits,n):
    if arr[0]!=0:
     v=int(''.join(map(str,arr)))
     if refs['_is_prime'](v):first.add(v)
  from sympy import primerange
  second={v for v in primerange(2,10**length) if len(set(str(v)))==len(str(v)) and set(str(v))<=set(map(str,digits))}
 else:
  first=refs['_parenthesized_values'](tuple(p['operands']),tuple(p['operators']))
  # Independent adjacent-reduction enumeration, not candidate or reference interval DP.
  def reduce_all(nums,ops):
   if len(nums)==1:return {nums[0]}
   values=set()
   for i,op in enumerate(ops):
    x,y=nums[i:i+2];z=x+y if op=='+' else x-y if op=='-' else x*y
    values.update(reduce_all(nums[:i]+[z]+nums[i+2:],ops[:i]+ops[i+1:]))
   return values
  second=reduce_all(list(map(Fraction,p['operands'])),p['operators'])
 if first!=second:raise ValueError('INDEPENDENT_ORACLE_DISAGREEMENT')
 return str(len(first))

def prepare(out,evidence,groups):
 refs=references();private={r['task_id']:r for r in map(json.loads,(DATA/'private/discovery.jsonl').read_text().splitlines())};known={'D':set(),'E':set()}
 for file in ['discovery.jsonl','design.jsonl']:
  for r in map(json.loads,(DATA/'private'/file).read_text().splitlines()):
   p=r.get('original_metadata',{}).get('parameters',{})
   if 'digits' in p:known['D'].add(fingerprint({'digits':sorted(p['digits']),'max_length':p['max_length']}))
   elif 'numbers' in p and 'operators' in p:known['E'].add(fingerprint({'operands':p['numbers'],'operators':p['operators']}))
 source=[]
 for group,ids in enumerate(groups):
  for e in evidence:
   if e['evidence_id'] not in ids:continue
   raw=private[e['task_id']];p=raw['original_metadata']['parameters'];family='D' if 'digits' in p else 'E';p={'digits':p['digits'],'max_length':p['max_length']} if family=='D' else {'operands':p['numbers'],'operators':p['operators']}
   answer=oracle(family,p,refs);assert answer==raw['gold_answer'];source.append(dict(case_id=e['task_id'],group=group,family=family,role='source',parameters=p,answer=answer,oracle_agreement=True))
 novel=[];rng=random.Random(20261028351)
 # Prespecified parameter-distribution coverage, before any new synthesis outcome.
 seeds={'D':[{'digits':[0],'max_length':1},{'digits':[2],'max_length':1},{'digits':[0,4,6,8],'max_length':4}],
 'E':[{'operands':[0],'operators':[]},{'operands':[-7],'operators':[]},{'operands':[5,5,2,7],'operators':['-','+','*']},{'operands':[0,2,0,3],'operators':['*','-','+']}]}
 for family in ['D','E']:
  seen=set(known[family]);accepted=[];attempt=0
  while len(accepted)<20:
   if attempt<len(seeds[family]):p=seeds[family][attempt]
   elif family=='D':
    n=rng.randint(3,8);p=dict(digits=sorted(rng.sample(range(10),n)),max_length=rng.randint(1,min(4,n)))
   else:
    n=rng.randint(2,8);p=dict(operands=[rng.randint(-9,15) for _ in range(n)],operators=[rng.choice(['+','-','*']) for _ in range(n-1)])
   attempt+=1;h=fingerprint(p)
   if h in seen:continue
   seen.add(h);answer=oracle(family,p,refs);r=dict(case_id=f'alg35-{family}-{len(accepted):02}',family=family,role='new_parameters',parameters=p,answer=answer,oracle_agreement=True,parameter_sha256=h);accepted.append(r)
  novel+=accepted
 invalid={'D':[{}, {'digits':[1,1,3],'max_length':2},{'digits':[-1,2],'max_length':1},{'digits':[1,10],'max_length':1},{'digits':[True,3],'max_length':1},{'digits':[1,2,3,4,5],'max_length':5}],
 'E':[{}, {'operands':[],'operators':[]},{'operands':[1,2],'operators':[]},{'operands':[1,2],'operators':['/']},{'operands':[1.5,2],'operators':['+']},{'operands':[True,2],'operators':['+']}]}
 invalidrows=[dict(case_id=f'alg35-{family}-invalid-{i}',family=family,role='invalid',parameters=p,answer=None) for family,pp in invalid.items() for i,p in enumerate(pp)]
 save(out/'private/cases.json',source+novel+invalidrows)
 save(out/'private/oracle_audit.json',dict(reference_path=str(REF),reference_sha256=sha(REF),oracle_agreement_cases=len(source)+len(novel),second_oracles=['sympy primerange with decimal-digit constraints','exhaustive adjacent-reduction tree enumeration'],private_only=True,candidate_not_oracle=True,unique_sources=12,unique_new_parameter_instances=40,distinct_computational_families=2,exclusion='P0 exposed Discovery/Design and source parameters. No P0 sealed Gate/Legacy/Fresh accessed. Not a claim of globally unseen natural original tasks.'))
