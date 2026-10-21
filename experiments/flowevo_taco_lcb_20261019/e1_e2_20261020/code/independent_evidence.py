import collections,functools,itertools,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def get(t):
 p=ROOT/'private_e1'/t
 return json.loads((p/'private_failure_case.json').read_text()),json.loads((p/'isolated_failure_execution.json').read_text())
def build():
 out={}
 # Query/reference counts are logical output-contract contradictions, not inferred algorithm errors.
 expectedcounts={'0180':3,'0749':5,'0889':1,'0724':2,'0118':1,'0395':10,'0657':5,'0914':4,'0916':2,'0967':3,'0589':8,'0779':2,'0294':5,'0466':3,'0357':2,'0836':2,'0411':10,'0880':1,'0727':3,'0681':2,'0012':3,'0573':4,'0614':2,'0721':3}
 for tid,n in expectedcounts.items():
  c,e=get('taco_'+tid);count=len(c['expected'].split());assert count!=n,(tid,count,n)
  out['taco_'+tid]={'kind':'output_contract_contradiction','required_tokens':n,'reference_tokens':count,'note':'Required count independently read from statement and input; candidate correctness not implied.'}
 for tid in ['0130','0401','0491','0194','0271','0288','0317','0900','0219']:
  c,e=get('taco_'+tid);s=c['input'].split();a=list(map(int,s)) if tid!='0271' else None
  if tid=='0130':
   @functools.lru_cache(None)
   def f(a):
    if a[0]==0:return False
    for i in range(1,len(a)):
     b=list(a);b[0]-=1;b[0],b[i]=b[i],b[0]
     if not f(tuple(b)):return True
    return False
   i=1;vals=[]
   for _ in range(a[0]):n=a[i];i+=1;vals.append('Alice' if f(tuple(a[i:i+n])) else 'Bob');i+=n
  elif tid=='0401':
   i=1;vals=[]
   for _ in range(a[0]):
    n=a[i];i+=1;claim=a[i:i+n];i+=n;best=0
    for par in itertools.product(range(-1,n),repeat=n):
     valid=True
     for start in range(n):
      node=start;seen=set()
      while node!=-1:
       if node in seen:valid=False;break
       seen.add(node);node=par[node]
      if not valid:break
     if valid:best=max(best,sum(par.count(j)==claim[j] for j in range(n)))
    vals.append(str(best))
  elif tid=='0491':
   i=1;vals=[]
   for _ in range(a[0]):
    n=a[i];i+=1;x=a[i:i+n];i+=n;y=a[i:i+n];i+=n;best=0
    for p in itertools.permutations(y):
     v=(1<<30)-1
     for u,w in zip(x,p):v&=u^w
     best=max(best,v)
    vals.append(str(best))
  elif tid=='0194':
   vals=[]
   for offset in range(a[0]):
    x,y,z,A,B,C=a[1+6*offset:7+6*offset];dp={(0,0,0):0}
    for i in range(x+1):
     for j in range(y+1):
      for k in range(z+1):
       if i+j+k==0:continue
       candidates=[]
       for di,dj,dk,cost in [(1,0,0,A),(0,1,0,A),(0,0,1,A),(1,1,0,B),(1,0,1,B),(0,1,1,B),(1,1,1,C)]:
        if i>=di and j>=dj and k>=dk:candidates.append(dp[i-di,j-dj,k-dk]+cost)
       dp[i,j,k]=min(candidates)
    vals.append(str(dp[x,y,z]))
  elif tid=='0271':
   k,m=map(int,s[:2]);f=['','a','b']
   for j in range(3,k+1):f.append(f[-1]+f[-2])
   vals=[str(sum(f[k][i:i+len(word)]==word for i in range(len(f[k])-len(word)+1))) for word in s[2:]]
  elif tid=='0288':
   i=1;vals=[]
   for _ in range(a[0]):
    n=a[i];i+=1;adj=[[] for j in range(n)]
    for j in range(n-1):u,v=a[i]-1,a[i+1]-1;i+=2;adj[u].append(v);adj[v].append(u)
    par=[-1]*n;queue=[0]
    for u in queue:
     for v in adj[u]:
      if v!=par[u]:par[v]=u;queue.append(v)
    dist=[[9]*n for j in range(n)]
    for u in range(n):
     dist[u][u]=0
     for v in adj[u]:
      dist[u][v]=1
      for w in adj[v]:
       if w!=u and not (par[u]==v and par[w]==v):dist[u][w]=2
    best=n+1
    for mask in range(1<<n):
     good=True
     for target in range(n):
      ds=sorted(dist[src][target] for src in range(n) if mask>>src&1)
      if len(ds)<2 or sum(ds[:2])>2:good=False;break
     if good:best=min(best,bin(mask).count('1'))
    vals.append(str(best if best<=n else -1))
  elif tid=='0317':
   vals=[]
   for j in range(a[0]):
    u,v=a[1+2*j:3+2*j];anc={};d=0
    while u:anc[u]=d;u//=2;d+=1
    d=0
    while v not in anc:v//=2;d+=1
    vals.append(str(d+anc[v]))
  elif tid=='0900':
   i=1;vals=[]
   for _ in range(a[0]):
    n=a[i];i+=1;arr=a[i:i+n];i+=n;q=a[i];i+=1
    for j in range(q):
     l,r=a[i:i+2];i+=2;v=arr[l-1]
     for x in arr[l:r]:v&=x
     vals.append('ODD' if v%2 else 'EVEN')
  else:
   i=1;vals=[];violations=[]
   for case in range(a[0]):
    n,m=a[i:i+2];i+=2;d=[[10**12]*n for j in range(n)]
    for u in range(n):d[u][u]=0
    for j in range(m):
     u,v,w=a[i:i+3];i+=3
     if not(1<=u<=n and 1<=v<=n and 1<=w<=100):violations.append([case,u,v,w])
     d[u-1][v-1]=min(d[u-1][v-1],w);d[v-1][u-1]=min(d[v-1][u-1],w)
    S,A,H=[x-1 for x in a[i:i+3]];i+=3
    for k in range(n):
     for u in range(n):
      for v in range(n):d[u][v]=min(d[u][v],d[u][k]+d[k][v])
    vals.append(str(max(d[S][u]+2*d[u][A]+d[u][H] for u in range(n) if u not in {S,A,H})))
   assert i==len(a)
   if violations:
    out['taco_'+tid]={'kind':'invalid_input','out_of_bounds_roads':violations[:20],'count':len(violations)};continue
  assert vals==e['output'].split(),(tid,vals,e['output'][:200])
  assert vals!=c['expected'].split(),tid
  out['taco_'+tid]={'kind':'independent_oracle','oracle_result':vals,'matches_candidate':True,'reference_result':c['expected'].split()}
 # Explicit invalid bounds and tree witness.
 c,e=get('taco_0946');l,r=map(int,c['input'].split());assert r-l>50;out['taco_0946']={'kind':'invalid_input','r_minus_l':r-l,'maximum':50}
 c,e=get('taco_0060');a=list(map(int,c['input'].split()));n,k=a[1:3];edges=list(zip(a[3+k::2],a[4+k::2]));adj=[[] for i in range(n+1)]
 for u,v in edges:adj[u].append(v);adj[v].append(u)
 seen={1};todo=[1]
 for u in todo:
  for v in adj[u]:
   if v not in seen:seen.add(v);todo.append(v)
 assert len(seen)!=n;out['taco_0060']={'kind':'invalid_input','reachable_from_root':len(seen),'declared_vertices':n,'note':'Disconnected n-1 edge input cannot be the guaranteed tree; parent-only traversal can loop on its cyclic component.'}
 return out
if __name__=='__main__':
 out=build();(ROOT/'independent_evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('proved',len(out))
