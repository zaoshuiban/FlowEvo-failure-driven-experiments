import hashlib,itertools,json,pathlib,sys,collections
from suite import accepts,honest_feasible,ROOT,BASE
from replay import evaluate
sys.path.insert(0,str(BASE/'repair_v2d_20261020/code'));from regrade import write

def checker_crosschecks():
 R=__import__('random').Random(20261024);count=0
 for n in [2,3]:
  for z in range(100):
   pairs=list(itertools.permutations(range(1,n+1),2));R.shuffle(pairs);rows=[(a,b,R.randrange(2)) for a,b in pairs[:R.randrange(len(pairs)+1)]];any_ok=False
   for D in itertools.product(range(2),repeat=n):
    brute=any(all((H[a-1]^H[b-1]^D[a-1])==c for a,b,c in rows) for H in itertools.product(range(2),repeat=n));assert honest_feasible(n,rows,D)==brute;any_ok|=brute;count+=1
   assert honest_feasible(n,rows)==any_ok
 def partitions(xs):
  if not xs:yield [];return
  a=xs[0]
  for pair in itertools.combinations(xs[1:],2):
   team=[a,*pair]
   for rest in partitions([x for x in xs if x not in team]):yield [team]+rest
 cases=json.loads((ROOT/'suite_frozen.json').read_text())['cases']
 for c in cases['taco_0617']:
  v=list(map(int,c['input'].split()));n,m=v[:2];edges=list(zip(v[2::2],v[3::2]));solutions=[]
  for part in partitions(list(range(1,n+1))):
   loc={x:i for i,p in enumerate(part) for x in p}
   if all(loc[a]==loc[b] for a,b in edges):solutions.append(part)
  assert bool(solutions)==bool(c['expected']);assert accepts('taco_0617',c,'-1')==(not solutions)
  if solutions:
   text=' '.join(str(x) for p in solutions[0] for x in p);assert accepts('taco_0617',c,text);assert accepts('taco_0617',c,' '.join(reversed(text.split())));assert not accepts('taco_0617',c,' '.join(['1']*n))
  count+=1
 binary=set()
 for n in range(1,9):
  for bits in itertools.product('01',repeat=n):binary.add(tuple(sum(bits[i]+bits[j]==p for i in range(n) for j in range(i+1,n)) for p in ['00','01','10','11']))
 for c in cases['taco_0936']:
  v=tuple(map(int,c['input'].split()));assert (c['expected'] is not None)==(v in binary);assert accepts('taco_0936',c,'Impossible')==(v not in binary);count+=1
 assert accepts('taco_0936',{'input':'0 0 0 0','expected':True,'comparison':'binary_pairs'},'0')
 assert accepts('taco_0936',{'input':'0 0 0 0','expected':True,'comparison':'binary_pairs'},'1')
 assert accepts('taco_0616',{'input':[5,14],'expected':[3,2],'comparison':'function'},[3.0,2.0])
 assert not accepts('taco_0616',{'input':[1,2],'expected':[1,0],'comparison':'function'},[True,0])
 assert not accepts('x',{'input':'','expected':'1 2 2','comparison':'tokens'},'2 1 2')
 return count

def main():
 checks=checker_crosschecks();suite=json.loads((ROOT/'suite_frozen.json').read_text())['cases'];catalog={x['task_id']:x for x in json.loads((BASE/'repair_v2_20261020/catalog.json').read_text())};report=[]
 for tid,cases in sorted(suite.items()):
  results=[json.loads(p.read_text()) for p in (ROOT/'verdicts'/tid).glob('*.json')];passing=[r for r in results if r['status']=='PASS']
  if passing:
   chosen=passing[0];old=next(BASE.glob('runs/*/'+tid+'/result.json'));reference=old.parent/(chosen['stage']+'.py')
  else:
   assert tid=='lcb_atcoder_abc399_e','No independently verified legal program: '+tid
   reference=next((BASE/'e1_e2_20261020/e2_results/programs').glob('*'+tid+'_R2_1.py'));positive=evaluate(tid,reference,cases,catalog[tid].get('function_name'));assert positive['passed'];chosen={'stage':'PREEXISTING_E2_R2_REFERENCE_NOT_HISTORICAL_2132','tested':positive['tested']}
  target=ROOT/'validated_references'/(tid+'.py');target.parent.mkdir(exist_ok=True);target.write_bytes(reference.read_bytes());fn=catalog[tid].get('function_name')
  wrong=ROOT/'wrong_program_fixtures'/(tid+'.py');wrong.parent.mkdir(exist_ok=True);wrong.write_text('def '+fn+'(*args):\n    return None\n' if fn else 'print("-999999")\n');negative=evaluate(tid,wrong,cases,fn);assert not negative['passed'],tid
  report.append({'task_id':tid,'dataset':catalog[tid]['dataset'],'difficulty':catalog[tid]['difficulty'],'task_sha256':catalog[tid]['task_sha256'],'input_scope':'frozen generated legal cases; small exhaustive domains plus explicit maximum-depth stress where stated','cases':len(cases),'comparison':cases[0]['comparison'],'oracle':cases[0].get('oracle','independent statement-derived enumeration/invariant, see suite.py and prior generators'),'positive_historical_stage':chosen['stage'],'positive_program_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),'positive_cases_passed':chosen['tested'],'wrong_program_status':negative['status'],'wrong_program_fixture_only':True})
 write(ROOT/'trusted_tasks.json',report);write(ROOT/'validation.json',{'accepted_tasks':len(report),'positive_programs_verified':len(report),'wrong_programs_rejected':len(report),'independent_checker_crosschecks':checks,'no_generated_mutant_is_historical_failure':True,'generation_calls':0});print('VALIDATED',len(report),'checker comparisons',checks)
if __name__=='__main__':main()
