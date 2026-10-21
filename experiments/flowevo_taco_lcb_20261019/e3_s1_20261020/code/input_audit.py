"""Independent statement-contract audit; unknown contracts are never called legal."""
import collections,importlib.util,json,math,pathlib,re,sys
from legal_suite import R,B,graph_components
class ContractError(ValueError):pass
def require(test,why):
 if not test:raise ContractError(why)
class Cursor:
 def __init__(self,text):self.tokens=text.split();self.i=0
 def take(self):
  require(self.i<len(self.tokens),'missing input tokens');x=self.tokens[self.i];self.i+=1;return x
 def num(self,lo=None,hi=None):
  try:x=int(self.take())
  except ValueError:raise ContractError('non-integer token')
  require((lo is None or x>=lo) and (hi is None or x<=hi),'integer outside statement range');return x
 def nums(self,n,lo=None,hi=None):return [self.num(lo,hi) for _ in range(n)]
 def done(self):require(self.i==len(self.tokens),'extra input tokens / wrong testcase count')
def tree(n,edges):require(len(edges)==n-1 and all(u!=v for u,v in edges) and len(graph_components(n,edges))==1,'not the guaranteed connected acyclic tree')
def acyclic(deps):
 indegree=list(map(len,deps));adj=[[] for _ in deps]
 for v,ps in enumerate(deps):
  require(len(ps)==len(set(ps)) and v not in ps,'duplicate/self prerequisites')
  for u in ps:adj[u].append(v)
 q=[i for i,x in enumerate(indegree) if x==0]
 for v in q:
  for u in adj[v]:
   indegree[u]-=1
   if indegree[u]==0:q.append(u)
 require(len(q)==len(deps),'cyclic prerequisite graph')
def audit(tid,inp):
 if tid=='taco_0191':
  require(isinstance(inp,list) and len(inp)==1 and len(inp[0])==2 and all(len(row)==2 for row in inp[0]),'vector shape')
  require(all(type(x) in [int,float] and math.isfinite(x) for row in inp[0] for x in row),'finite vector coordinates');return
 if not isinstance(inp,str):raise NotImplementedError('legacy function-input contract not re-audited here')
 s=Cursor(inp)
 if tid in ['taco_0543','taco_0572']:
  n=s.num(1 if tid=='taco_0543' else 2,100000 if tid=='taco_0543' else 300000)
  if tid=='taco_0572':colors=s.nums(n,0,2);require(1 in colors and 2 in colors,'missing required red or blue vertex')
  edges=[(s.num(1,n)-1,s.num(1,n)-1) for _ in range(n-1)];tree(n,edges)
 elif tid=='taco_0486':
  n=s.num(1,200);s.nums(n,1,3);deps=[]
  for i in range(n):deps.append([x-1 for x in s.nums(s.num(0,n-1),1,n)])
  acyclic(deps)
 elif tid=='lcb_atcoder_abc315_e':
  n=s.num(2,200000);deps=[]
  for i in range(n):deps.append([x-1 for x in s.nums(s.num(0,n-1),1,n)])
  require(deps[0] and sum(map(len,deps))<=200000,'required dependencies / total edge limit');acyclic(deps)
 elif tid=='lcb_atcoder_abc314_d':
  n=s.num(1,500000);text=s.take();require(len(text)==n and re.fullmatch('[a-zA-Z]+',text),'string length/alphabet');q=s.num(1,500000)
  for _ in range(q):
   t=s.num(1,3);x=s.num();c=s.take();require(re.fullmatch('[a-zA-Z]',c),'operation letter')
   require((1<=x<=n) if t==1 else (x==0 and c=='a'),'operation sentinel contract')
 elif tid=='lcb_atcoder_abc371_f':
  n=s.num(1,200000);xs=s.nums(n,0,10**8);require(all(x<y for x,y in zip(xs,xs[1:])),'strictly ordered positions');q=s.num(1,200000)
  for _ in range(q):s.num(1,n);s.num(0,10**8)
 elif tid=='taco_0215':
  n=s.num(1,1000);height=s.num(1,10**9);s.nums(n,1,height)
 elif tid=='taco_0138':n=s.num(1,1000000);s.nums(n,1,10**9)
 elif tid=='taco_0917':
  n=s.num(1,200000);b=s.num(1,n)
  for i in range(1,n+1):s.num(0,n-i)
  q=s.num(1,100000);s.nums(q,1,b-1)
 elif tid=='taco_0112':
  a,b=s.take(),s.take();require(1<=len(a)<=200000 and len(a)==len(b) and re.fullmatch('[a-z]+',a+b),'equal lowercase strings')
 elif tid=='taco_0517':
  n=s.num(1,2000);q=s.num(1,10000);angles=s.nums(q,0,100000);require(all(x%90==0 for x in angles),'angle multiple of 90')
 elif tid=='taco_0995':
  n=s.num(1,1000);s.nums(n*n,0,1);q=s.num(1,1000000)
  for _ in range(q):
   t=s.num(1,3)
   if t!=3:s.num(1,n)
 elif tid=='taco_0711':
  n=s.num(1,100000);m=s.num(0,min(100000,n*(n-1)//2));s.nums(n,0,10**9)
  for _ in range(m):s.num(1,n);s.num(1,n)
 elif tid=='taco_0284':
  n=s.num(1,200000);ss=[s.take() for _ in range(n)];require(sum(map(len,ss))<=1000000 and all(1<=len(v)<=50 and re.fullmatch('[a-z]+',v) for v in ss),'password alphabet/length')
 elif tid=='taco_0985':
  n=s.num(3,50);m=s.num(1,50);ss=[s.take() for _ in range(n)];require(all(len(v)==m and re.fullmatch('[a-z0-9#*&]+',v) for v in ss),'password rows')
  feasible=any(i!=j and i!=k and j!=k and any(c.isdigit() for c in ss[i]) and any(c.islower() for c in ss[j]) and any(c in '#*&' for c in ss[k]) for i in range(n) for j in range(n) for k in range(n));require(feasible,'valid password not attainable')
 elif tid=='taco_0664':
  n=s.num(1,100000);s.num(1,100000);p=s.num(1,100000);s.nums(n,0,1);ops=s.take();require(len(ops)==p and not set(ops)-set('!?'),'request length/alphabet')
 elif tid=='taco_0533':
  n=s.num(1,200000);m=s.num(0,min(200000,n*(n-1)//2));edges=[tuple(sorted((s.num(1,n),s.num(1,n)))) for _ in range(m)];require(all(u!=v for u,v in edges) and len(set(edges))==m,'missing-edge uniqueness / no self-loop')
 elif tid=='taco_0730':
  m=s.num(1);edges=[(s.num(1,30000),s.num(1,30000)) for _ in range(m)];left=max(u for u,v in edges);right=min(v for u,v in edges);mx=max(max(e) for e in edges)
  require(left<right and any(max(u,v)==mx for u,v in edges) and max(left,(mx+1)//2)<=min(15000,right-1),'no valid bipartition bound N')
 else:
  max_t={'taco_0357':120000,'taco_0403':1000,'taco_0702':10000,'taco_0303':5,'taco_0457':1000,'taco_0318':10000,'taco_0511':1000,'taco_0915':5,'taco_0121':100,'taco_0313':10000,'taco_0646':10,'taco_0777':1000,'taco_0193':100,'taco_0966':10,'taco_0429':5,'taco_0445':1000,'taco_0838':10,'taco_0721':5}
  if tid not in max_t:raise NotImplementedError('prior-suite contract or unaudited task')
  t=s.num(1,max_t[tid]);total_n=0;total_max=0
  for _ in range(t):
   if tid in ['taco_0357','taco_0318','taco_0313','taco_0721']:
    n=s.num(2 if tid=='taco_0721' else 1,50 if tid=='taco_0318' else 100000);s.nums(n,1,10**8 if tid=='taco_0721' else 10**9);total_n+=n
   elif tid=='taco_0403':
    n=s.num(2,200000);a=s.nums(n,1,200000);require(len(set(a))==n,'distinct array elements');total_n+=n;total_max+=max(a)
   elif tid in ['taco_0702','taco_0303']:
    n=s.num(2 if tid=='taco_0702' else 1,100000 if tid=='taco_0702' else 500000)
    if tid=='taco_0303':k=s.num(1,2);require(k<=n,'ranking requests nonexistent pair (statement ambiguity)')
    tree(n,[(s.num(1,n)-1,s.num(1,n)-1) for _ in range(n-1)]);total_n+=n
   elif tid=='taco_0457':
    m,n=s.num(1,1000),s.num(1,1000);s.num(0,m-1);s.num(0,n-1)
   elif tid=='taco_0838':require(re.fullmatch('[rgb]{1,100000}',s.take()),'container alphabet/length')
   elif tid=='taco_0511':
    n=s.num(1,100000);k=s.num(1,min(100,n));a=s.nums(n,0,10**9);moves=s.nums(k,1,n);require(len(set(a))==n and len(set(moves))==k and 1 in moves,'distinct discs/moves; required move 1');total_n+=n
   elif tid=='taco_0915':
    n=s.num(1,100000);q=s.num(1,100000);s.nums(n,1,1000000)
    for _ in range(q):l=s.num(1,n);r=s.num(l,n);s.num(1,r-l+1)
   elif tid=='taco_0121':n=s.num(1,100);s.num(1,n);s.nums(n,1,n)
   elif tid=='taco_0646':lo=s.num(1,10**9);hi=s.num(lo,10**9);require(hi-lo<=100000,'prime interval too wide')
   elif tid=='taco_0777':
    n=s.num(1,1000000);s.num(1,n);total_n+=n
    for _ in range(n):lo=s.num(0,n-1);s.num(lo,n-1)
   elif tid=='taco_0193':lo=s.num(1,100000);s.num(lo,100000)
   elif tid=='taco_0966':n=s.num(1,100000);s.nums(n,0,10**9);s.num(0,10**9)
   elif tid=='taco_0429':
    n=s.num(1,100000);q=s.num(1,100000);sizes=[]
    for _ in range(n):a=s.num(1,100000);sizes.append(a);s.nums(a,1,1000)
    require(sum(sizes)<=100000,'total cycle vertices')
    for i in range(n):s.num(1,sizes[i]);s.num(1,sizes[(i+1)%n]);s.num(1,1000)
    for _ in range(q):
     v1,c1,v2,c2=s.num(),s.num(1,n),s.num(),s.num(1,n);require(c1!=c2 and 1<=v1<=sizes[c1-1] and 1<=v2<=sizes[c2-1],'distinct cycle endpoints / vertex bounds')
   elif tid=='taco_0445':
    n=s.num(2,100000);a=s.nums(n,-1,1000000);signs=s.take();require(len(signs)==n-1 and not set(signs)-set('<>='),'scraped relation symbols or length corrupted');total_n+=n
    for i,c in enumerate(signs):
     if a[i]>=0 and a[i+1]>=0:require(a[i]<a[i+1] if c=='<' else a[i]>a[i+1] if c=='>' else a[i]==a[i+1],'violates adjacent-known guarantee')
  caps={'taco_0403':300000,'taco_0702':200000,'taco_0303':500000,'taco_0357':1000000,'taco_0313':100000,'taco_0511':100000,'taco_0777':1000000,'taco_0445':1000000}
  if tid in caps:require(total_n<=caps[tid],'sum N exceeds constraint')
  if tid=='taco_0403':require(total_max<=300000,'sum max(A) exceeds constraint')
 s.done()
def main():
 suite=json.loads((R/'public_suite.json').read_text())['cases'];prior_path=B/'trusted_rgf_20261020/code';sys.path.insert(0,str(prior_path))
 spec=importlib.util.spec_from_file_location('prior_contract_audit',prior_path/'contracts_audit.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 output=[]
 for tid,cases in suite.items():
  for i,c in enumerate(cases):
   try:
    if c['comparison']=='prior':old.audit(tid,c['prior_case'])
    else:audit(tid,c['input'])
   except Exception as exc:raise AssertionError((tid,i,type(exc).__name__,str(exc)))
  task=json.loads((R/'source/tasks'/(tid+'.json')).read_text());io=task['input_output'];io=json.loads(io) if isinstance(io,str) else io
  findings=[];unknown=0;checked=0
  for i,inp in enumerate(io['inputs']):
   try:audit(tid,inp);checked+=1
   except NotImplementedError:unknown+=1
   except (ValueError,IndexError,TypeError) as exc:checked+=1;findings.append({'case_index':i,'finding':str(exc),'input_contract_invalid':True})
  output.append({'task_id':tid,'public_cases_verified':len(cases),'public_scope':cases[0]['contract_scope'],'legacy_cases_total':len(io['inputs']),'legacy_contract_checked':checked,'legacy_contract_unknown':unknown,'legacy_invalid_cases':len(findings),'legacy_findings':findings,'raw_references_trusted':False})
 (R/'input_contract_review.json').write_text(json.dumps(output,ensure_ascii=False,indent=2));print('Contracts PASS',len(output),'tasks',sum(x['public_cases_verified'] for x in output),'public cases; legacy invalid',sum(x['legacy_invalid_cases'] for x in output))
if __name__=='__main__':main()
