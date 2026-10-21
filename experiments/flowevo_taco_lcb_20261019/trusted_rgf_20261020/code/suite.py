"""Frozen legal-input scoring suite. No generation APIs, hidden benchmark labels or answers."""
import collections,itertools,json,math,pathlib,random,re,hashlib,functools
from decimal import Decimal
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
MULTI=set('0180 0130 0914 0491 0294 0967 0962 0812 0583 0337 0900 0055 0401 0657'.split())
def split_multi(tid,text,expected):
 a=text.split();i=0;count=int(a[i]);i+=1;out=[];outputs=str(expected).split();j=0
 def take(n):
  nonlocal i
  v=a[i:i+n];assert len(v)==n;i+=n;return v
 def num():return int(take(1)[0])
 for _ in range(count):
  start=i;required=1;valid=True
  if tid in ['0180','0294']:x,y=map(int,take(2));valid=x>=1 and y>=1 and (tid!='0294' or x>y)
  elif tid in ['0130','0914','0401']:n=num();arr=list(map(int,take(n)));valid=n>=(2 if tid=='0130' else 1) and all(0<=x<n for x in arr) if tid=='0401' else n>=(2 if tid=='0130' else 1) and min(arr)>=1
  elif tid=='0491':n=num();arr=list(map(int,take(2*n)));valid=n>=1 and all(0<=x<2**30 for x in arr)
  elif tid=='0967':n,A,B=map(int,take(3));arr=list(map(int,take(n)));valid=n>=1 and 1<=A<=n and 1<=B<=n and all(1<=x<=n for x in arr)
  elif tid=='0962':s=take(1)[0];valid=1<=len(s)<=100 and bool(re.fullmatch('[a-z]+',s))
  elif tid=='0812':n,m=map(int,take(2));q=list(map(int,take(m)));valid=1<=n<=m and set(q)==set(range(1,n+1))
  elif tid=='0583':
   n,initial=map(int,take(2));rows=[list(map(int,take(3))) for z in range(n)];valid=1<=n<=100 and all(1<=t and l<=h for t,l,h in rows) and all(rows[z][0]<=rows[z+1][0] for z in range(n-1))
  elif tid=='0337':n=num();rows=take(n);valid=1<=n<=50 and all(len(s)==n and not set(s)-{'0','1'} for s in rows)
  elif tid=='0900':n=num();arr=list(map(int,take(n)));q=num();rows=[list(map(int,take(2))) for z in range(q)];required=q;valid=all(1<=l<=r<=n for l,r in rows) and min(arr)>=1
  elif tid=='0055':
   n,m=map(int,take(2));v=take(n);s=take(1)[0];w=take(m);t=take(1)[0];valid=n>=1 and m>=1 and len(s)==n and len(t)==m and 'D' in t and not set(s+t)-{'A','D'} and min(map(int,v+w))>=1
  elif tid=='0657':
   n=num();d=[]
   for z in range(n):m=num();d+=list(map(int,take(m)));valid=valid and m>=1
   valid=valid and n>=1 and min(d)>=1
  else:raise ValueError(tid)
  exp=outputs[j:j+required];j+=required;assert len(exp)==required
  if valid:out.append({'input':'1\n'+layout(tid,a[start:i])+'\n','expected':' '.join(exp),'comparison':'float' if tid=='0967' else 'tokens'})
 assert i==len(a) and j==len(outputs)
 return out

def layout(tid,b):
 if tid in ['0180','0294','0962']:return ' '.join(b)
 if tid in ['0130','0914','0401']:return b[0]+'\n'+' '.join(b[1:])
 if tid=='0491':
  n=int(b[0]);return b[0]+'\n'+' '.join(b[1:1+n])+'\n'+' '.join(b[1+n:])
 if tid=='0967':return ' '.join(b[:3])+'\n'+' '.join(b[3:])
 if tid=='0812':return ' '.join(b[:2])+'\n'+' '.join(b[2:])
 if tid=='0583':return ' '.join(b[:2])+'\n'+'\n'.join(' '.join(b[i:i+3]) for i in range(2,len(b),3))
 if tid=='0337':return '\n'.join(b)
 if tid=='0900':
  n=int(b[0]);return b[0]+'\n'+' '.join(b[1:1+n])+'\n'+b[n+1]+'\n'+'\n'.join(' '.join(b[i:i+2]) for i in range(n+2,len(b),2))
 if tid=='0055':
  n,m=map(int,b[:2]);return ' '.join(b[:2])+'\n'+' '.join(b[2:2+n])+'\n'+b[2+n]+'\n'+' '.join(b[3+n:3+n+m])+'\n'+b[-1]
 if tid=='0657':
  rows=[b[0]];i=1
  for z in range(int(b[0])):
   m=int(b[i]);rows.append(' '.join(b[i:i+m+1]));i+=m+1
  return '\n'.join(rows)
 raise ValueError(tid)

def is_subseq(a,s):
 it=iter(s);return all(any(x==c for x in it) for c in a)
def transform(s,t):
 from e2_oracles import transform as f
 return f(s,t)
def honest_feasible(n,rows,confused=None):
 # Independent BFS parity constraints, not the historical weighted DSU.
 size=2*n if confused is None else n;g=[[] for _ in range(size)]
 for a,b,c in rows:
  a-=1;b-=1
  u,v,w=(a,n+b,c) if confused is None else (a,b,c^int(confused[a]))
  g[u].append((v,w));g[v].append((u,w))
 seen={}
 for root in range(size):
  if root in seen:continue
  seen[root]=0;q=[root]
  for u in q:
   for v,w in g[u]:
    want=seen[u]^w
    if v in seen:
     if seen[v]!=want:return False
    else:seen[v]=want;q.append(v)
 return True

def accepts(tid,case,actual):
 kind=case.get('comparison','tokens');exp=case['expected']
 if kind=='function':
  def no_bool(x):return all(no_bool(v) for v in x) if isinstance(x,(list,tuple)) else not isinstance(x,bool)
  return actual==exp and no_bool(actual)
 if not isinstance(actual,str):return False
 got=actual.split()
 if kind=='float':
  try:return len(got)==len(str(exp).split()) and all(Decimal(x).is_finite() and abs(Decimal(x)-Decimal(y))<=(Decimal('0.00001') if tid=='lcb_atcoder_abc314_e' else Decimal('0.000001'))*max(1,abs(Decimal(y))) for x,y in zip(got,str(exp).split()))
  except Exception:return False
 if kind=='tokens':
  target=str(exp).split()
  if tid in {'taco_0130','taco_0294','taco_0583','taco_0337','taco_0962'}:got=[x.lower() for x in got];target=[x.lower() for x in target]
  return got==target
 try:
  a=list(map(int,case['input'].split()))
  if kind=='teams':
   n,m=a[:2];edges=list(zip(a[2::2],a[3::2]));parts=exp
   if got==['-1']:return not parts
   nums=list(map(int,got));assert len(nums)==n and set(nums)==set(range(1,n+1));where={x:i//3 for i,x in enumerate(nums)};return all(where[u]==where[v] for u,v in edges)
  if kind=='binary_pairs':
   counts=a
   if got==['Impossible']:return exp is None
   if len(got)!=1 or not re.fullmatch('[01]+',got[0]) or len(got[0])>1000000:return False
   seen=[0,0];sums=[0]*4
   for c in got[0]:
    x=int(c)
    for y in (0,1):sums[y*2+x]+=seen[y]
    seen[x]+=1
   return sums==counts
  if kind=='partition':
   n=a[0];nums=list(map(int,got));diff,k=nums[:2];v=nums[2:];return len(v)==k and 0<k<n and len(set(v))==k and all(1<=x<=n for x in v) and abs(n*(n+1)//2-2*sum(v))==diff==n*(n+1)//2%2
  if kind=='honest':
   n,m=a[:2];rows=[a[2+3*i:5+3*i] for i in range(m)]
   if got==['-1']:return not honest_feasible(n,rows)
   return len(got)==1 and len(got[0])==n and not set(got[0])-{'0','1'} and honest_feasible(n,rows,got[0])
 except (ValueError,AssertionError,IndexError):return False
 return False

def additions(seed):
 R=random.Random(seed);out=collections.defaultdict(list)
 def add(t,inp,exp,kind='tokens'):out[t].append({'input':inp,'expected':exp,'comparison':kind,'provenance':'statement-domain independent generator seed '+str(seed)})
 for _ in range(100):
  x,y,z=[R.randrange(1,6) for i in range(3)];A,B,C=[R.randrange(1,12) for i in range(3)];dp={(0,0,0):0}
  for i in range(x+1):
   for j in range(y+1):
    for k in range(z+1):
     if i+j+k:dp[i,j,k]=min(dp[i-di,j-dj,k-dk]+cost for di,dj,dk,cost in [(1,0,0,A),(0,1,0,A),(0,0,1,A),(1,1,0,B),(1,0,1,B),(0,1,1,B),(1,1,1,C)] if i>=di and j>=dj and k>=dk)
  add('taco_0194',f'1\n{x} {y} {z} {A} {B} {C}\n',str(dp[x,y,z]))
 for k in range(1,18):
  f=['','a','b']
  for j in range(3,k+1):f.append(f[-1]+f[-2])
  words=[''.join(R.choice('ab') for z in range(R.randrange(1,9))) for i in range(8)];ans=[sum(f[k][i:i+len(w)]==w for i in range(len(f[k])-len(w)+1)) for w in words];add('taco_0271',f'{k} 8\n'+'\n'.join(words)+'\n','\n'.join(map(str,ans)))
 for _ in range(100):
  pairs=[(R.randrange(1,1000),R.randrange(1,1000)) for j in range(10)];ans=[]
  for x,y in pairs:
   ax={};d=0
   while x:ax[x]=d;x//=2;d+=1
   d=0
   while y not in ax:y//=2;d+=1
   ans.append(ax[y]+d)
  add('taco_0317','10\n'+'\n'.join(f'{a} {b}' for a,b in pairs),'\n'.join(map(str,ans)))
 for h,l in [(-1,0),(0,0),(0,2),(5,14),(72,201)]+[(R.randrange(-2,20),R.randrange(-2,81)) for z in range(100)]:
  valid=[(c,h-c) for c in range(max(0,h)+1) if h>=0 and h-c>=0 and 2*c+4*(h-c)==l];add('taco_0616',[h,l],list(valid[0]) if valid else 'No solutions','function')
 for _ in range(75):
  n=R.choice([3,6,9]);edges=[(a,b) for a in range(1,n+1) for b in range(a+1,n+1) if R.randrange(5)==0];components=[];seen=set()
  for u in range(1,n+1):
   if u in seen:continue
   q=[u];seen.add(u)
   for v in q:
    for a,b in edges:
     w=b if a==v else a if b==v else -1
     if w>0 and w not in seen:seen.add(w);q.append(w)
   components.append(q)
  sizes=collections.Counter(map(len,components));possible=max(map(len,components))<=3 and sizes[1]>=sizes[2]
  add('taco_0617',f'{n} {len(edges)}\n'+'\n'.join(f'{u} {v}' for u,v in edges),possible,'teams')
 # Exhaustive small binary strings are an independent feasibility catalogue.
 binary={}
 for n in range(1,9):
  for bits in itertools.product('01',repeat=n):
   s=''.join(bits);c=[sum(s[i]+s[j]==p for i in range(n) for j in range(i+1,n)) for p in ['00','01','10','11']];binary.setdefault(tuple(c),s)
 for counts in list(binary)[:80]+[tuple(R.randrange(10) for i in range(4)) for j in range(60)]:
  # Any solution here has at most 8 chars except count-ambiguous singletons; use triangular roots for true feasibility.
  roots=lambda v:[n for n in range(11) if n*(n-1)//2==v]
  possible=any(n+m>=1 and n*m==counts[1]+counts[2] for n in roots(counts[0]) for m in roots(counts[3]));add('taco_0936',' '.join(map(str,counts)),True if possible else None,'binary_pairs')
 for _ in range(100):
  n=R.randrange(1,51);t=R.randrange(1,51);s=''.join(R.choice('BG') for z in range(n));cur=s
  for j in range(t):
   nxt=list(cur)
   for i in range(n-1):
    if cur[i:i+2]=='BG':nxt[i]='G';nxt[i+1]='B'
   cur=''.join(nxt)
  add('taco_0333',f'{n} {t}\n{s}\n',cur)
 for n in list(range(2,40))+[60000]:add('taco_0831',str(n),str(n*(n+1)//2%2),'partition')
 # Long valid forests expose recursion-resource implementation bugs, not malformed cycles.
 for n in [1,2,30,990,1000,1100,1500,2000]:
  for reverse in [False,True]:
   parents=list(range(2,n+1))+[-1] if reverse else [-1]+list(range(1,n));add('taco_0875',str(n)+'\n'+'\n'.join(map(str,parents)),str(n))
 for _ in range(75):
  n=R.randrange(1,35);p=[-1]+[R.randrange(-1,i) for i in range(1,n)];depth=[]
  for i in range(n):
   z=i;d=0
   while z!=-1:d+=1;z=p[z]
   depth.append(d)
  add('taco_0875',str(n)+'\n'+'\n'.join(str(z+1 if z>=0 else -1) for z in p),str(max(depth)))
 letters='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
 words=['AAAA','AAaA','AaAA','DD??S','?D??S','abcd','A'*26,'A'*30]
 words+=[''.join(R.choice('ABab?') for z in range(R.randrange(4,9))) for i in range(45)]
 for s in words:
  if s.count('?')>2:continue
  ans=0
  for values in itertools.product(letters,repeat=s.count('?')):
   it=iter(values);w=''.join(next(it) if c=='?' else c for c in s);bad=any(w[i]==w[j] and w[i].isupper() and w[k].islower() and w[l].isupper() for i,j,k,l in itertools.combinations(range(len(w)),4));ans+=not bad
  add('lcb_atcoder_abc301_f',s+'\n',str(ans%998244353))
 for _ in range(90):
  n=R.randrange(2,7);pairs=list(itertools.permutations(range(1,n+1),2));R.shuffle(pairs);rows=[(u,v,R.randrange(2)) for u,v in pairs[:R.randrange(len(pairs)+1)]];add('lcb_atcoder_arc188_c',f'{n} {len(rows)}\n'+'\n'.join(' '.join(map(str,r)) for r in rows),honest_feasible(n,rows),'honest')
 for _ in range(90):
  n=R.randrange(1,12);s=''.join(R.choice('abcd') for i in range(n));t=''.join(R.choice('abcd') for i in range(n));add('lcb_atcoder_abc399_e',f'{n}\n{s}\n{t}\n',str(transform(s,t)))
 from fractions import Fraction
 for _ in range(70):
  n=R.randrange(1,4);m=R.randrange(1,10);wheels=[]
  for j in range(n):
   c=R.randrange(1,10);v=[R.randrange(min(6,m+1)) for z in range(R.randrange(1,6))]
   if not any(v):v[-1]=1
   wheels.append((c,v))
  @functools.lru_cache(None)
  def dp(need):
   if need<=0:return Fraction(0)
   return min((c*len(v)+sum((dp(need-x) for x in v if x),Fraction(0)))/sum(x>0 for x in v) for c,v in wheels)
  ans=dp(m);add('lcb_atcoder_abc314_e',f'{n} {m}\n'+'\n'.join(f'{c} {len(v)} '+' '.join(map(str,v)) for c,v in wheels),str(float(ans)),'float')
 return dict(out)

def build():
 import sys;sys.path.insert(0,str(BASE/'e1_e2_20261020/code'))
 tests=collections.defaultdict(list);rejected=collections.Counter()
 for name in ['public_tests_frozen.json','public_tests_extra_frozen.json']:
  for tid,cases in json.loads((BASE/'e1_e2_20261020'/name).read_text())['tests'].items():
   for case in cases:
    if tid[5:] in MULTI:
     atomic=split_multi(tid[5:],case['input'],case['expected']);tests[tid]+=atomic
     if not atomic:rejected[tid]+=1
    else:tests[tid].append({**case,'comparison':'tokens'})
 tests.update(additions(20261022));assert len(tests)==35,len(tests)
 for tid,cases in tests.items():
  unique={json.dumps(c['input'],sort_keys=True):c for c in cases};cases=sorted(unique.values(),key=lambda c:hashlib.sha256(json.dumps(c['input']).encode()).hexdigest())
  # Freeze complete stress boundaries for recursion cases, all small cases for new oracles.
  tests[tid]=cases if tid=='taco_0875' else cases[:120]
 payload={'seed':20261022,'scope':'finite audited legal inputs, not full-domain equivalence','cases':dict(tests),'prior_invalid_generator_batches_removed':dict(rejected)}
 p=ROOT/'suite_frozen.json';assert not p.exists() or json.loads(p.read_text())==payload;p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(len(tests),sum(map(len,tests.values())))
if __name__=='__main__':build()
