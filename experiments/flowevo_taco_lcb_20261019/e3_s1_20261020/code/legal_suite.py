"""Statement-derived public legal probes. No historical test inputs are sampled."""
import collections,functools,heapq,itertools,json,math,pathlib,random
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1];B=R.parent
def graph_components(n,edges):
 g=[[] for _ in range(n)]
 for u,v in edges:g[u].append(v);g[v].append(u)
 seen=set();parts=[]
 for u in range(n):
  if u in seen:continue
  seen.add(u);q=[u]
  for v in q:
   for w in g[v]:
    if w not in seen:seen.add(w);q.append(w)
  parts.append(q)
 return parts
def playlist(a):
 ids=list(range(len(a)));i=0;last=None;stale=0;out=[]
 while ids and stale<=2*len(ids)+2:
  u=ids[i]
  if last is not None and math.gcd(a[last],a[u])==1:
   out.append(u+1);ids.pop(i);last=None;stale=0
   if ids:i%=len(ids)
  else:last=u;i=(i+1)%len(ids);stale+=1
 return [len(out)]+out
def tree_orders(n,edges):
 ans=[]
 for root in range(n):
  g=[[] for _ in range(n)]
  for u,v in edges:g[u].append(v);g[v].append(u)
  parent=[-1]*n;order=[root];parent[root]=root
  for u in order:
   for v in g[u]:
    if parent[v]<0:parent[v]=u;order.append(v)
  count=0
  for p in itertools.permutations(range(n)):
   pos={v:i for i,v in enumerate(p)}
   if all(v==root or pos[v]<pos[parent[v]] for v in range(n)):count+=1
  ans.append(count)
 return ans
def min_bamboo(n,edges):
 kept=0
 for mask in range(1<<len(edges)):
  if bin(mask).count('1')<=kept:continue
  deg=[0]*n
  for i,(u,v) in enumerate(edges):
   if mask>>i&1:deg[u]+=1;deg[v]+=1
  if max(deg)<=2:kept=bin(mask).count('1')
 return n-1-kept
def accepts(tid,c,actual):
 kind=c.get('comparison','tokens')
 if kind=='prior':
  import sys
  sys.path.insert(0,str(B/'trusted_rgf_20261020/code'))
  from suite import accepts as old
  return old(tid,c['prior_case'],actual)
 if kind=='numeric_function':
  def same(x,y):
   if isinstance(x,bool):return False
   if isinstance(y,list):return isinstance(x,list) and len(x)==len(y) and all(same(a,b) for a,b in zip(x,y))
   if isinstance(y,(int,float)):return isinstance(x,(int,float)) and math.isfinite(x) and abs(x-y)<=c.get('tol',1e-7)
   return x==y
  return same(actual,c['expected'])
 if kind=='float':
  try:v=float(str(actual).strip());return math.isfinite(v) and abs(v-float(c['expected']))<=c.get('tol',1e-6)*max(1,abs(float(c['expected'])))
  except (ValueError,TypeError):return False
 if kind=='bamboo':
  try:
   vals=list(map(int,str(actual).split()));k=vals[0];n=c['meta']['n'];edges={tuple(sorted(e)) for e in c['meta']['edges']}
   if k!=int(c['expected']) or len(vals)!=1+4*k:return False
   for i in range(k):
    u,v,x,y=vals[1+4*i:5+4*i];u-=1;v-=1;x-=1;y-=1
    if not all(0<=z<n for z in [u,v,x,y]) or u==v or x==y:return False
    old=tuple(sorted((u,v)));new=tuple(sorted((x,y)))
    if old not in edges:return False
    edges.remove(old)
    if new in edges:return False
    edges.add(new)
   deg=[0]*n
   for u,v in edges:deg[u]+=1;deg[v]+=1
   return max(deg)<=2 and len(graph_components(n,edges))==1
  except (ValueError,IndexError,TypeError):return False
 if kind=='topological':
  try:
   order=list(map(int,str(actual).split()));deps=c['meta']['deps'];needed=set();q=list(deps[0])
   while q:
    u=q.pop()
    if u not in needed:needed.add(u);q+=deps[u]
   if len(order)!=len(needed) or {v-1 for v in order}!=needed:return False
   seen=set()
   for v in order:
    v-=1
    if not set(deps[v])<=seen:return False
    seen.add(v)
   return True
  except (ValueError,IndexError):return False
 a=str(actual).split();e=str(c['expected']).split()
 return ([x.casefold() for x in a]==[x.casefold() for x in e]) if kind=='casefold' else a==e
def cases_for(tid,seed=20261020):
 rng=random.Random(str(seed)+'|S1|'+tid);out=[]
 def add(inp,exp,kind='tokens',meta=None,scope='LEGAL_STATEMENT_DOMAIN'):
  out.append({'input':inp,'expected':exp if isinstance(exp,(list,dict)) or kind=='numeric_function' else str(exp),'comparison':kind,'meta':meta or {},'contract_scope':scope,'provenance':'independent statement-domain generator; seed '+str(seed)})
 prior=json.loads((B/'trusted_rgf_20261020/suite_frozen.json').read_text())['cases']
 if tid in prior:
  for c in prior[tid]:out.append({**c,'comparison':'prior','prior_case':c,'contract_scope':'PREVIOUSLY_AUDITED_FINITE_LEGAL_SUITE','provenance':'reused frozen trusted suite, not a new independent dataset'})
  return out
 for rep in range(32):
  if tid=='taco_0191':
   points=[[rng.randint(-100,100)/rng.choice([1,10]) for _ in range(2)] for _ in range(2)];v=math.sqrt(sum((points[0][i]-points[1][i])**2 for i in range(2)));add([points],v,'numeric_function')
  elif tid=='taco_0721':
   a=[rng.randint(1,100) for _ in range(rng.randint(2,12))];z=0
   for i in range(len(a)):
    v=0
    for j in range(i,len(a)):v^=a[j];z^=v
   add('1\n'+str(len(a))+'\n'+' '.join(map(str,a))+'\n',z)
  elif tid=='taco_0357':
   a=[rng.randint(1,20) for _ in range(rng.randint(1,7))];z=10**9
   for i in range(len(a)):
    other=a[:i]+a[i+1:]
    for denomination in range(1,max(a)+1):
     if all(v%denomination==0 for v in other):z=min(z,1+sum(v//denomination for v in other))
   add('1\n'+str(len(a))+'\n'+' '.join(map(str,a))+'\n',z)
  elif tid=='lcb_atcoder_abc314_d':
   n=rng.randint(1,12);s=''.join(rng.choice('aAbBcC') for _ in range(n));a=list(s);ops=[]
   for _ in range(rng.randint(1,30)):
    typ=rng.randint(1,3);pos=rng.randrange(n);ch=rng.choice('aAbBcC');ops.append((typ,pos+1,ch) if typ==1 else (typ,0,'a'))
    if typ==1:a[pos]=ch
    else:a=list(''.join(a).lower() if typ==2 else ''.join(a).upper())
   add(str(n)+'\n'+s+'\n'+str(len(ops))+'\n'+'\n'.join(' '.join(map(str,x)) for x in ops)+'\n',''.join(a))
  elif tid=='lcb_atcoder_abc315_e':
   n=rng.randint(2,10);rank=list(range(n));rng.shuffle(rank)
   if rank.index(0)==0:rank[0],rank[-1]=rank[-1],rank[0]
   deps=[[] for _ in range(n)]
   for i in range(n):deps[rank[i]]=[rank[j] for j in range(i) if rng.random()<.3]
   if not deps[0]:deps[0]=[rank[0]]
   inp=str(n)+'\n'+'\n'.join(str(len(v))+(' '+' '.join(str(x+1) for x in v) if v else '') for v in deps)+'\n';add(inp,'semantic','topological',{'deps':deps})
  elif tid=='lcb_atcoder_abc371_f':
   n=rng.randint(1,10);a=sorted(rng.sample(range(30),n));initial=a[:];ops=[];cost=0
   for _ in range(rng.randint(1,20)):
    i=rng.randrange(n);target=rng.randint(0,35);ops.append((i+1,target));before=a[:];a[i]=target
    if target>before[i]:
     for j in range(i+1,n):a[j]=max(a[j],a[j-1]+1)
    else:
     for j in range(i-1,-1,-1):a[j]=min(a[j],a[j+1]-1)
    cost+=sum(abs(x-y) for x,y in zip(a,before))
   add(str(n)+'\n'+' '.join(map(str,initial))+'\n'+str(len(ops))+'\n'+'\n'.join(f'{i} {g}' for i,g in ops)+'\n',cost)
  elif tid in ['taco_0543','taco_0572','taco_0702','taco_0303']:
   n=rng.randint(2,7);edges=[(rng.randrange(v),v) for v in range(1,n)];g=[[] for _ in range(n)]
   for u,v in edges:g[u].append(v);g[v].append(u)
   edge_text='\n'.join(f'{u+1} {v+1}' for u,v in edges)+'\n'
   if tid=='taco_0543':
    def walk(u,p,depth,prob):
     children=[v for v in g[u] if v!=p]
     return prob*depth if not children else sum(walk(v,u,depth+1,prob/len(children)) for v in children)
    add(str(n)+'\n'+edge_text,float(walk(0,-1,0,Fraction(1))),'float')
   elif tid=='taco_0572':
    colors=[rng.randint(0,2) for _ in range(n)];colors[0]=1;colors[-1]=2;z=0
    for removed in edges:
     parts=graph_components(n,[e for e in edges if e!=removed]);z+=all(not ({1,2}<={colors[v] for v in part}) for part in parts)
    add(str(n)+'\n'+' '.join(map(str,colors))+'\n'+edge_text,z)
   elif tid=='taco_0702':add('1\n'+str(n)+'\n'+edge_text,min_bamboo(n,edges),'bamboo',{'n':n,'edges':edges})
   else:
    k=rng.randint(1,2);counts=tree_orders(n,edges);ranking=sorted([(v,i+1) for i,v in enumerate(counts)],reverse=True);v,u=ranking[k-1];add('1\n'+f'{n} {k}\n'+edge_text,f'{u} {v}')
  elif tid=='taco_0403':
   a=rng.sample(range(1,35),rng.randint(2,8));z=1
   while any(abs(a[i]-a[j])%z==0 for i in range(len(a)) for j in range(i)):z+=1
   add('1\n'+str(len(a))+'\n'+' '.join(map(str,a))+'\n',z)
  elif tid=='taco_0838':
   s=''.join(rng.choice('rgb') for _ in range(rng.randint(1,8)));z=10**9
   for perm in itertools.permutations('rgb'):
    target=''.join(c*s.count(c) for c in perm);positions={c:collections.deque(i for i,v in enumerate(target) if v==c) for c in 'rgb'};p=[positions[c].popleft() for c in s];z=min(z,sum(p[i]>p[j] for i in range(len(p)) for j in range(i+1,len(p))))
   add('1\n'+s+'\n',z)
  elif tid=='taco_0138':
   a=[rng.randint(1,6) for _ in range(rng.randint(1,4))]
   @functools.lru_cache(None)
   def win(state):return any(not win(state[:i]+(v,)+state[i+1:]) for i,x in enumerate(state) for v in range(x))
   z=sum(not win(tuple(a[:i]+[v]+a[i+1:])) for i,x in enumerate(a) for v in range(x));add(str(len(a))+'\n'+' '.join(map(str,a))+'\n',z)
  elif tid=='taco_0486':
   n=rng.randint(1,8);colors=[rng.randrange(3) for _ in range(n)];perm=list(range(n));rng.shuffle(perm);deps=[[] for _ in range(n)]
   for i in range(n):deps[perm[i]]=[perm[j] for j in range(i) if rng.random()<.3]
   dp={(0,c):0 for c in range(3)}
   for mask in range(1<<n):
    for cur in range(3):
     if (mask,cur) not in dp:continue
     for v in range(n):
      if not mask>>v&1 and all(mask>>p&1 for p in deps[v]):
       k=(mask|1<<v,colors[v]);dp[k]=min(dp.get(k,10**9),dp[mask,cur]+1+(colors[v]-cur)%3)
   z=min(dp.get(((1<<n)-1,c),10**9) for c in range(3));add(str(n)+'\n'+' '.join(str(c+1) for c in colors)+'\n'+'\n'.join(str(len(d))+(' '+' '.join(str(v+1) for v in d) if d else '') for d in deps)+'\n',z)
  elif tid=='taco_0215':
   n=rng.randint(1,8);height=rng.randint(1,20);a=[rng.randint(1,height) for _ in range(n)]
   @functools.lru_cache(None)
   def shelves(vs):
    if not vs:return 0
    return min([vs[0]+shelves(vs[1:])]+[max(vs[0],vs[j])+shelves(vs[1:j]+vs[j+1:]) for j in range(1,len(vs))])
   z=max(k for k in range(1,n+1) if shelves(tuple(a[:k]))<=height);add(f'{n} {height}\n'+' '.join(map(str,a))+'\n',z)
  elif tid=='taco_0917':
   n=rng.randint(2,12);b=rng.randint(2,n);reach=[rng.randint(0,n-i-1) for i in range(n)];dp=[0]*n;dp[b-1]=1
   for i in range(b-2,-1,-1):dp[i]=sum(dp[i+1:i+1+reach[i]])%1000000007
   queries=[rng.randint(1,b-1) for _ in range(8)];add(f'{n} {b}\n'+'\n'.join(map(str,reach))+'\n8\n'+'\n'.join(map(str,queries))+'\n','\n'.join(str(dp[q-1]) for q in queries))
  elif tid=='taco_0457':
   x,y=rng.randint(1,20),rng.randint(1,20);p,q=rng.randint(0,10),rng.randint(0,10)
   @functools.lru_cache(None)
   def win(a,b):return any(not win(i,b) for i in range(a)) or any(not win(a,j) for j in range(b)) or any(not win(a-d,b-d) for d in range(1,min(a,b)+1))
   add(f'1\n{x+p} {y+q} {p} {q}\n','Alice' if win(x,y) else 'Bob','casefold')
  elif tid=='taco_0112':
   n=rng.choice([1,2,3,4,6,8,12]);a=''.join(rng.choice('ab') for _ in range(n));b=''.join(rng.choice('ab') for _ in range(n))
   @functools.lru_cache(None)
   def eq(a,b):return a==b or (len(a)%2==0 and ((eq(a[:len(a)//2],b[:len(b)//2]) and eq(a[len(a)//2:],b[len(b)//2:])) or (eq(a[:len(a)//2],b[len(b)//2:]) and eq(a[len(a)//2:],b[:len(b)//2]))))
   add(a+'\n'+b+'\n','YES' if eq(a,b) else 'NO')
  elif tid=='taco_0318':
   a=[rng.randint(1,50) for _ in range(rng.randint(1,8))];n=len(a);reachable=[]
   for x in a:
    vals=[]
    while x:
     if x<=n:vals.append(x)
     x//=2
    reachable.append(vals)
   @functools.lru_cache(None)
   def match(i,mask):return i==n or any(not mask>>v&1 and match(i+1,mask|1<<v) for v in reachable[i])
   add('1\n'+str(n)+'\n'+' '.join(map(str,a))+'\n','YES' if match(0,0) else 'NO','casefold')
  elif tid=='taco_0517':
   n=rng.randint(1,9);h=[0,1,0,1]
   for k in range(4,n**4+1):h.append((h[k-1]+2*h[k-2]+3*h[k-3])%2)
   a=[[h[((i+1)*(j+1))**2] for j in range(n)] for i in range(n)];angles=[0,90,180,270,360,450,990];ans=[]
   for angle in angles:
    b=[row[:] for row in a]
    for _ in range((angle//90)%4):b=[list(row) for row in zip(*b[::-1])]
    ans.append(sum(a[i][j]!=b[i][j] for i in range(n) for j in range(n)))
   add(f'{n} {len(angles)}\n'+'\n'.join(map(str,angles))+'\n','\n'.join(map(str,ans)))
  elif tid=='taco_0995':
   n=rng.randint(1,6);a=[[rng.randrange(2) for _ in range(n)] for _ in range(n)];initial=[r[:] for r in a];ops=[];ans=[]
   for _ in range(15):
    typ=rng.randint(1,3);i=rng.randrange(n);ops.append(str(typ) if typ==3 else f'{typ} {i+1}')
    if typ==1:a[i]=[1-v for v in a[i]]
    elif typ==2:
     for row in a:row[i]=1-row[i]
    else:ans.append(str(sum(a[i][j]*a[j][i] for i in range(n) for j in range(n))%2))
   add(str(n)+'\n'+'\n'.join(' '.join(map(str,row)) for row in initial)+'\n'+str(len(ops))+'\n'+'\n'.join(ops)+'\n',''.join(ans))
  elif tid=='taco_0511':
   n=rng.randint(1,9);a=rng.sample(range(12),n);moves=sorted(set([1]+[rng.randint(1,n) for _ in range(rng.randint(0,n-1))]));score=[2**x for x in a]
   @functools.lru_cache(None)
   def best(i):return 0 if i==n else max(sum(score[i:i+k])-best(i+k) for k in moves if i+k<=n)
   v=best(0);add('1\n'+f'{n} {len(moves)}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,moves))+'\n','Chef' if v>0 else 'Garry' if v<0 else 'Draw')
  elif tid in ['taco_0711','taco_0533','taco_0730']:
   n=rng.randint(1,9);possible=list(itertools.combinations(range(n),2));rng.shuffle(possible);edges=possible[:rng.randint(0,len(possible))]
   if tid=='taco_0711':
    a=[rng.randint(0,4) for _ in range(n)];parts=graph_components(n,edges);z=math.prod(sum(a[u]==max(a[v] for v in p) for u in p) for p in parts)%1000000007;add(f'{n} {len(edges)}\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges)+'\n',z)
   elif tid=='taco_0533':
    missing=set(edges);parts=graph_components(n,[e for e in possible if e not in missing]);sizes=sorted(map(len,parts));add(f'{n} {len(edges)}\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges)+'\n',str(len(parts))+'\n'+' '.join(map(str,sizes)))
   else:
    edges=[(rng.randrange(n),rng.randrange(n,2*n)) for _ in range(n)];edges[-1]=(rng.randrange(n),2*n-1);sizes=[len(p) for p in graph_components(2*n,edges) if len(p)>1];add(str(n)+'\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges)+'\n',f'{min(sizes)} {max(sizes)}')
  elif tid=='taco_0915':
   n=rng.randint(1,12);a=[rng.randint(1,3) for _ in range(n)];queries=[];answers=[]
   for _ in range(12):
    l=rng.randrange(n);r=rng.randrange(l,n);k=rng.randint(1,r-l+1);queries.append((l+1,r+1,k));answers.append(sum(len(list(g))>=k for _,g in itertools.groupby(a[l:r+1])))
   add('1\n'+f'{n} {len(queries)}\n'+' '.join(map(str,a))+'\n'+'\n'.join(' '.join(map(str,q)) for q in queries)+'\n','\n'.join(map(str,answers)))
  elif tid=='taco_0284':
   ss=[''.join(rng.choice('abcdef') for _ in range(rng.randint(1,5))) for _ in range(rng.randint(1,10))];edges=[(i,j) for i in range(len(ss)) for j in range(i) if set(ss[i])&set(ss[j])];add(str(len(ss))+'\n'+'\n'.join(ss)+'\n',len(graph_components(len(ss),edges)))
  elif tid=='taco_0121':
   n=rng.randint(1,12);k=rng.randint(1,n);a=[rng.randint(1,n) for _ in range(n)];add('1\n'+f'{n} {k}\n'+' '.join(map(str,a))+'\n',sum(a.count(i)>=k and a[i-1]!=i for i in range(1,n+1)))
  elif tid=='taco_0313':
   a=[rng.randint(1,12) for _ in range(rng.randint(1,10))];add('1\n'+str(len(a))+'\n'+' '.join(map(str,a))+'\n',' '.join(map(str,playlist(a))))
  elif tid=='taco_0985':
   n,m=rng.randint(3,6),rng.randint(1,5);ss=[''.join(rng.choice('ab01#*&') for _ in range(m)) for _ in range(n)];z=10**9
   for i,ch in enumerate('0a#'):
    j=rng.randrange(m);ss[i]=ss[i][:j]+ch+ss[i][j+1:]
   for pos in itertools.product(range(m),repeat=n):
    selected=[ss[i][j] for i,j in enumerate(pos)]
    if any(c.isdigit() for c in selected) and any(c.islower() for c in selected) and any(c in '#*&' for c in selected):z=min(z,sum(min(j,m-j) for j in pos))
   add(f'{n} {m}\n'+'\n'.join(ss)+'\n',z)
  elif tid=='taco_0664':
   n=rng.randint(1,10);k=rng.randint(1,15);a=[rng.randrange(2) for _ in range(n)];initial=a[:];ops=''.join(rng.choice('!?') for _ in range(20));ans=[]
   for op in ops:
    if op=='!':a=a[-1:]+a[:-1]
    else:ans.append(max(sum(a[i:i+min(k,n)]) for i in range(n-min(k,n)+1)))
   add(f'{n} {k} {len(ops)}\n'+' '.join(map(str,initial))+'\n'+ops+'\n','\n'.join(map(str,ans)))
  elif tid=='taco_0646':
   lo=rng.randint(1,200);hi=lo+rng.randint(0,80);ans=[x for x in range(lo,hi+1) if x>=2 and all(x%d for d in range(2,math.isqrt(x)+1))];add(f'1\n{lo} {hi}\n','\n'.join(map(str,ans)))
  elif tid=='taco_0777':
   n=rng.randint(1,10);height=rng.randint(1,n);gaps=[]
   for _ in range(n):lo=rng.randrange(n);gaps.append((lo,rng.randrange(lo,n)))
   z=min(sum(not lo<=row<=hi for lo,hi in gaps for row in range(start,start+height)) for start in range(n-height+1));add('1\n'+f'{n} {height}\n'+'\n'.join(f'{lo} {hi}' for lo,hi in gaps)+'\n',z)
  elif tid=='taco_0193':
   lo=rng.randint(1,1000);hi=lo+rng.randint(0,200);add(f'1\n{lo} {hi}\n',sum(x%10 in [2,3,9] for x in range(lo,hi+1)))
  elif tid=='taco_0966':
   a=[rng.randrange(32) for _ in range(rng.randint(1,12))];x=rng.randrange(32);add('1\n'+str(len(a))+'\n'+' '.join(map(str,a))+'\n'+str(x)+'\n',sum(((u^v)&x)==0 for u in a for v in a))
  elif tid=='taco_0429':
   n=rng.randint(2,5);sizes=[rng.randint(1,4) for _ in range(n)];offset=[0]
   for s in sizes:offset.append(offset[-1]+s)
   total=offset[-1];g=[[] for _ in range(total)];lines=[]
   def edge(u,v,w):g[u].append((v,w));g[v].append((u,w))
   for i,s in enumerate(sizes):
    ws=[rng.randint(1,10) for _ in range(s)];lines.append(str(s)+' '+' '.join(map(str,ws)))
    for j,w in enumerate(ws):edge(offset[i]+j,offset[i]+(j+1)%s,w)
   connections=[]
   for i in range(n):
    j=(i+1)%n;u=rng.randrange(sizes[i]);v=rng.randrange(sizes[j]);w=rng.randint(1,10);connections.append(f'{u+1} {v+1} {w}');edge(offset[i]+u,offset[j]+v,w)
   queries=[];answers=[]
   for _ in range(12):
    i,j=rng.sample(range(n),2);u=rng.randrange(sizes[i]);v=rng.randrange(sizes[j]);queries.append(f'{u+1} {i+1} {v+1} {j+1}');dist=[10**9]*total;dist[offset[i]+u]=0;q=[(0,offset[i]+u)]
    while q:
     d,k=heapq.heappop(q)
     if d!=dist[k]:continue
     for t,w in g[k]:
      if d+w<dist[t]:dist[t]=d+w;heapq.heappush(q,(d+w,t))
    answers.append(dist[offset[j]+v])
   add('1\n'+f'{n} {len(queries)}\n'+'\n'.join(lines+connections+queries)+'\n','\n'.join(map(str,answers)))
  elif tid=='taco_0445':
   # Corrupted scraped constraints/examples: conditional checks cannot certify a program defect.
   n=rng.randint(2,6);known=[rng.choice([-1,0,1,2,3]) for _ in range(n)];s=''.join(rng.choice('<>=') for _ in range(n-1))
   def consistent(a):return all((x<y if c=='<' else x>y if c=='>' else x==y) for x,y,c in zip(a,a[1:],s))
   # Enforce the stated guarantee for adjacent known values.
   if any(known[i]>=0 and known[i+1]>=0 and not (known[i]<known[i+1] if s[i]=='<' else known[i]>known[i+1] if s[i]=='>' else known[i]==known[i+1]) for i in range(n-1)):continue
   possible=any(consistent(a) for a in itertools.product(*([v] if v>=0 else range(10) for v in known)))
   add('1\n'+str(n)+'\n'+' '.join(map(str,known))+'\n'+s+'\n','YES' if possible else 'NO','casefold',scope='CONDITIONAL_ON_RESTORED_RELATION_SYMBOLS')
  else:raise KeyError(tid)
 return out
def main():
 m=json.loads((R/'review_manifest.json').read_text());cases={t['task_id']:cases_for(t['task_id']) for t in m['tasks']}
 assert len(cases)==48 and all(cases.values())
 (R/'public_suite.json').write_text(json.dumps({'seed':20261020,'new_model_calls':0,'historical_hidden_inputs_used_for_generation':False,'cases':cases},ensure_ascii=False,indent=2))
 print('Public independent suite',len(cases),'tasks',sum(map(len,cases.values())),'cases')
if __name__=='__main__':main()
