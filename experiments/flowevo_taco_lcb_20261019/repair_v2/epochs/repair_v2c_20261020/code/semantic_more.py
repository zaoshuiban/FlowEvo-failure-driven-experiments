import bisect,collections,heapq,math
from semantic_extra import DSU
MORE_SUPPORTED=set('taco_0173 taco_0295 taco_0221 taco_0083 taco_0119 taco_0408 taco_0621 taco_0343 taco_0238 taco_0477'.split())
def lakes(grid):
 n=len(grid);m=len(grid[0]);seen=set();sizes=[]
 for i in range(n):
  for j in range(m):
   if grid[i][j]!='.' or (i,j) in seen:continue
   seen.add((i,j));q=[(i,j)];size=0;border=False
   while q:
    r,c=q.pop();size+=1;border|=r in (0,n-1) or c in (0,m-1)
    for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
     rr,cc=r+dr,c+dc
     if 0<=rr<n and 0<=cc<m and grid[rr][cc]=='.' and (rr,cc) not in seen:seen.add((rr,cc));q.append((rr,cc))
   if not border:sizes.append(size)
 return sorted(sizes)

def decode(s):
 order=''.join(dict.fromkeys(reversed(s)))[::-1];counts=collections.Counter(s);length=0
 for i,ch in enumerate(order):
  if counts[ch]%(i+1):return False
  length+=counts[ch]//(i+1)
 original=s[:length];cur=original;pieces=[]
 for ch in order:pieces.append(cur);cur=cur.replace(ch,'')
 return ''.join(pieces)==s

def parse_more(tid,inp):
 from semantic import Cursor,require
 c=Cursor(inp)
 if tid=='taco_0173':
  t=c.one();d=c.take(t,False);require(t>=1 and all(s and s.isascii() and s.isalpha() and s.islower() for s in d),'input string alphabet')
 elif tid=='taco_0295':
  n,m=c.take(2);edges=[c.take(2) for _ in range(m)];topics=c.take(n);require(n>=1 and all(1<=x<=n for x in topics) and all(1<=u<=n and 1<=v<=n and u!=v for u,v in edges) and len({tuple(sorted(e)) for e in edges})==m,'blog graph bounds');d=(n,edges,topics)
 elif tid=='taco_0221':
  n=c.one();pairs=[c.take(2) for _ in range(n)];require(1<=n<=2000 and all(0<=p<=n and 0<=v<n for p,v in pairs),'tree/rank bounds');roots=[i for i,(p,_) in enumerate(pairs) if p==0];require(len(roots)==1,'single root');children=[[] for _ in range(n)]
  for i,(p,_) in enumerate(pairs):
   if p:children[p-1].append(i)
  order=[];stack=[roots[0]]
  while stack:
   u=stack.pop();order.append(u);require(len(order)<=n,'cycle');stack.extend(children[u])
  require(len(order)==n,'disconnected parent graph');sizes=[1]*n
  for u in reversed(order):
   if pairs[u][0]:sizes[pairs[u][0]-1]+=sizes[u]
  d=(pairs,children,order,sizes)
 elif tid=='taco_0083':
  n,m=c.take(2);edges=[c.take(3) for _ in range(m)];require(n>=1 and all(1<=u<=n and 1<=v<=n and u!=v and b in (0,1) for u,v,b in edges) and len({tuple(sorted((u,v))) for u,v,b in edges})==m,'road graph bounds');d=(n,edges)
 elif tid=='taco_0119':
  d=c.take(2);require(all(1<=x<=100 for x in d),'rectangle bounds')
 elif tid=='taco_0408':
  n,m,k=c.take(3);rows=[c.take(m) for _ in range(n)];require(1<=n<=1000 and 1<=m<=100 and k in (0,1) and all(1<=v<=10**6 for row in rows for v in row),'sort-network dimensions/range');d=(n,m,k,rows)
 elif tid=='taco_0621':
  t=c.one();d=c.take(t);require(t>=1 and all(2<=x<=10**9 for x in d),'bacteria mass bounds')
 elif tid=='taco_0343':
  n=c.one();require(1<=n<=10,'slot count');slots=[]
  for _ in range(n):
   count=c.one();a=c.take(count);require(1<=count<=200000 and all(1<=x<=10**8 for x in a) and all(a[i]<a[i+1] for i in range(count-1)),'item strengths/order');slots.append(a)
  m=c.one();banned={tuple(c.take(n)) for _ in range(m)};require(m>=0 and len(banned)==m and all(all(1<=v<=len(slots[i]) for i,v in enumerate(row)) for row in banned),'banned build range/uniqueness');require(math.prod(map(len,slots))>m,'all builds banned')
  start=tuple(map(len,slots));best=sum(a[-1] for a in slots);heap=[(-best,start)];seen={start}
  while heap:
   score,row=heapq.heappop(heap)
   if row not in banned:best=-score;break
   for i,v in enumerate(row):
    if v>1:
     neighbor=row[:i]+(v-1,)+row[i+1:]
     if neighbor not in seen:seen.add(neighbor);heapq.heappush(heap,(score+slots[i][v-1]-slots[i][v-2],neighbor))
  d=(slots,banned,best)
 elif tid=='taco_0238':
  n,m,k=c.take(3);grid=c.take(n,False);require(1<=n<=50 and 1<=m<=50 and 0<=k<=50 and all(len(r)==m and not set(r)-set('.*') for r in grid),'lake grid bounds');sizes=lakes(grid);require(len(sizes)>=k,'fewer initial lakes than k');d=(n,m,k,grid,sum(sizes[:len(sizes)-k]))
 elif tid=='taco_0477':
  n=c.one();p=c.take(n);require(1<=n<=100000 and sorted(p)==list(range(1,n+1)),'invalid permutation');d=p
 c.end();return d

def accepts_more(tid,d,out):
 a=out.split()
 if tid=='taco_0173':
  cursor=0
  for target in d:
   first=a[cursor];cursor+=1
   if first=='-1':
    if decode(target):return False
   else:
    order=a[cursor];cursor+=1
    if len(set(order))!=len(order) or set(order)!=set(first):return False
    pieces=[];cur=first
    for ch in order:pieces.append(cur);cur=cur.replace(ch,'')
    if ''.join(pieces)!=target:return False
  return cursor==len(a)
 if tid=='taco_0221':
  pairs,children,order,sizes=d;n=len(pairs)
  if a==['NO']:return any(v>=sizes[i] for i,(p,v) in enumerate(pairs))
  if not a or a[0]!='YES' or len(a)!=n+1:return False
  values=list(map(int,a[1:]));sub=[[] for _ in range(n)]
  if any(not 1<=v<=10**9 for v in values):return False
  for u in reversed(order):
   row=sorted(v for child in children[u] for v in sub[child])
   if bisect.bisect_left(row,values[u])!=pairs[u][1]:return False
   bisect.insort(row,values[u]);sub[u]=row
  return True
 if tid=='taco_0083':
  n,edges=d
  if a==['Impossible']:
   adjacency=[[] for _ in range(n)];colors=[None]*n
   for u,v,b in edges:adjacency[u-1].append((v-1,1-b));adjacency[v-1].append((u-1,1-b))
   for i in range(n):
    if colors[i] is not None:continue
    colors[i]=0;stack=[i]
    while stack:
     u=stack.pop()
     for v,parity in adjacency[u]:
      if colors[v] is None:colors[v]=colors[u]^parity;stack.append(v)
      elif colors[v]!=(colors[u]^parity):return True
   return False
  x=list(map(int,a));days=x[0];visits=collections.Counter(x[1:]);return 0<=days<=n and len(x)==days+1 and all(1<=u<=n for u in x[1:]) and all((b^(visits[u]%2)^(visits[v]%2))==1 for u,v,b in edges)
 if tid=='taco_0477':
  n=len(d);lengths=[];seen=set()
  for i in range(n):
   if i in seen:continue
   size=0
   while i not in seen:seen.add(i);size+=1;i=d[i]-1
   lengths.append(size)
  possible=1 in lengths or (2 in lengths and all(size%2==0 for size in lengths))
  if a==['NO']:return not possible
  if not a or a[0]!='YES' or len(a)!=1+2*(n-1):return False
  values=list(map(int,a[1:]));edges=set();ds=DSU(n)
  for u,v in zip(values[::2],values[1::2]):
   if not (1<=u<=n and 1<=v<=n and ds.join(u-1,v-1)):return False
   edges.add(tuple(sorted((u,v))))
  return all(tuple(sorted((d[u-1],d[v-1]))) in edges for u,v in edges)
 if tid=='taco_0238':
  n,m,k,original,optimum=d;count=int(a[0]);grid=a[1:]
  return len(grid)==n and all(len(r)==m and not set(r)-set('.*') for r in grid) and all(not (old=='*' and new=='.') for oldrow,newrow in zip(original,grid) for old,new in zip(oldrow,newrow)) and count==optimum==sum(old!=new for oldrow,newrow in zip(original,grid) for old,new in zip(oldrow,newrow)) and len(lakes(grid))==k
 x=list(map(int,a))
 if tid=='taco_0295':
  n,edges,topics=d;adj=[[] for _ in range(n)]
  for u,v in edges:adj[u-1].append(v-1);adj[v-1].append(u-1)
  if x==[-1]:
   return any(topics[u] in {topics[v] for v in adj[u]} or len({topics[v] for v in adj[u] if topics[v]<topics[u]})!=topics[u]-1 for u in range(n))
  if sorted(x)!=list(range(1,n+1)):return False
  written=[0]*n
  for u in x:
   u-=1;present={written[v] for v in adj[u]};mex=1
   while mex in present:mex+=1
   if mex!=topics[u]:return False
   written[u]=mex
  return True
 if tid=='taco_0119':
  n,m=d;k=x[0];points=list(zip(x[1::2],x[2::2]));return k==min(n,m)+1 and len(x)==1+2*k and len(set(points))==k and all(0<=u<=n and 0<=v<=m and u+v>0 for u,v in points) and all(math.isqrt((u-r)**2+(v-s)**2)**2!=(u-r)**2+(v-s)**2 for i,(u,v) in enumerate(points) for r,s in points[i+1:])
 if tid=='taco_0408':
  n,m,k,rows=d;count=x[0]
  if not (0<=count<=m*(m-1)//2 and len(x)==1+2*count):return False
  pairs=list(zip(x[1::2],x[2::2]))
  if any(not(1<=i<=m and 1<=j<=m and i!=j) for i,j in pairs):return False
  for original in rows:
   row=original[:]
   for i,j in pairs:
    if row[i-1]>row[j-1]:row[i-1],row[j-1]=row[j-1],row[i-1]
   if row!=sorted(row,reverse=bool(k)):return False
  return True
 if tid=='taco_0621':
  offset=0
  for mass in d:
   days=x[offset];offset+=1
   if days!=mass.bit_length()-1:return False
   splits=x[offset:offset+days];offset+=days
   if len(splits)!=days:return False
   count=1;total=1
   for value in splits:
    if not 0<=value<=count:return False
    count+=value;total+=count
   if total!=mass:return False
  return offset==len(x)
 if tid=='taco_0343':
  slots,banned,best=d
  return len(x)==len(slots) and all(1<=v<=len(slots[i]) for i,v in enumerate(x)) and tuple(x) not in banned and sum(slots[i][v-1] for i,v in enumerate(x))==best
 raise KeyError(tid)
