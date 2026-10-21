"""Additional constructive contracts; each validates objective as well as feasibility."""
import collections
EXTRA_SUPPORTED=set('taco_0649 taco_0485 taco_0577 taco_0205 taco_0220 taco_0308 taco_0984 taco_0639'.split())
class DSU:
 def __init__(self,n):self.p=list(range(n));self.count=n
 def find(self,u):
  while self.p[u]!=u:self.p[u]=self.p[self.p[u]];u=self.p[u]
  return u
 def join(self,u,v):
  a,b=self.find(u),self.find(v)
  if a==b:return False
  self.p[a]=b;self.count-=1;return True

def parse_extra(tid,inp):
 from semantic import Cursor,require
 c=Cursor(inp)
 if tid=='taco_0649':
  count=c.one();require(1<=count<=100,'test count');d=[]
  for _ in range(count):
   n,m=c.take(2);strings=c.take(n,False);require(1<=n<=10 and 1<=m<=10 and all(len(s)==m and s.isascii() and s.isalpha() and s.islower() for s in strings),'word dimensions/alphabet');d.append((m,strings))
 elif tid=='taco_0485':
  n=c.one();edges=[c.take(2) for _ in range(n-1)];colors=c.take(n);require(2<=n<=100000 and all(1<=x<=100000 for x in colors),'tree/color bounds');dsu=DSU(n)
  for u,v in edges:require(1<=u<=n and 1<=v<=n and dsu.join(u-1,v-1),'not a tree')
  d=(n,[(u,v) for u,v in edges if colors[u-1]!=colors[v-1]])
 elif tid=='taco_0577':
  count=c.one();d=[c.take(3) for _ in range(count)];require(1<=count<=20 and all(1<=l<=r<=500000 and 1<=m<=10**10 for l,r,m in d),'encryption bounds')
 elif tid=='taco_0205':
  n=c.one();d=c.take(n);require(1<=n<=100000 and len(set(d))==n and all(abs(x)<=10**9 for x in d),'distinct sequence bounds')
 elif tid=='taco_0220':
  n=c.one();a=c.take(2*n);require(1<=n<=100 and all(10<=x<=99 for x in a),'cube bounds');d=(n,a)
 elif tid=='taco_0308':
  n,m1,m2=c.take(3);require(1<=n<=1000 and 0<=m1<n and 0<=m2<n,'forest dimensions');e1=[c.take(2) for _ in range(m1)];e2=[c.take(2) for _ in range(m2)]
  for edges in (e1,e2):
   ds=DSU(n)
   for u,v in edges:require(1<=u<=n and 1<=v<=n and ds.join(u-1,v-1),'input is not a forest')
  d=(n,e1,e2)
 elif tid=='taco_0984':
  d=c.take(1,False)[0];require(1<=len(d)<=1000 and not set(d)-{'0','1'},'tile sequence bounds/alphabet')
 elif tid=='taco_0639':
  n,x,y=c.take(3);a=c.take(n);require(2<=n<=300000 and 1<=x<=10**9 and 1<=y<=10**9 and all(1<=v<=10**9 for v in a),'server bounds');d=(n,x,y,a)
 c.end();return d

def accepts_extra(tid,d,out):
 a=out.split()
 if tid=='taco_0649':
  if len(a)!=len(d):return False
  for answer,(m,strings) in zip(a,d):
   def valid(s):return len(s)==m and all(sum(x!=y for x,y in zip(s,t))<=1 for t in strings)
   if answer=='-1':
    first=strings[0]
    if valid(first):return False
    for i in range(m):
     for ch in 'abcdefghijklmnopqrstuvwxyz':
      if valid(first[:i]+ch+first[i+1:]):return False
   elif not (answer.isascii() and answer.isalpha() and answer.islower() and valid(answer)):return False
  return True
 if tid=='taco_0485':
  n,bad=d;candidates=set(range(1,n+1)) if not bad else set(bad[0])
  for edge in bad:candidates.intersection_update(edge)
  if a==['NO']:return not candidates
  return len(a)==2 and a[0]=='YES' and int(a[1]) in candidates
 if tid=='taco_0639':
  n,x,y,capacities=d
  if a==['No']:
   arr=sorted(capacities,reverse=True)
   def feasible(first,second):
    size=next((i+1 for i,v in enumerate(arr) if (i+1)*v>=first),None)
    return size is not None and any((j-size+1)*arr[j]>=second for j in range(size,n))
   return not (feasible(x,y) or feasible(y,x))
  if not a or a[0]!='Yes':return False
  values=list(map(int,a[1:]));k1,k2=values[:2];indices=values[2:]
  return k1>0 and k2>0 and len(indices)==k1+k2 and len(set(indices))==len(indices) and all(1<=i<=n for i in indices) and min(capacities[i-1] for i in indices[:k1])*k1>=x and min(capacities[i-1] for i in indices[k1:])*k2>=y
 x=list(map(int,a))
 if tid=='taco_0577':return len(x)==3*len(d) and all(l<=aa<=r and l<=b<=r and l<=cc<=r and m-b+cc>0 and (m-b+cc)%aa==0 for (l,r,m),(aa,b,cc) in zip(d,zip(x[::3],x[1::3],x[2::3])))
 if tid=='taco_0205':
  n=len(d);rank={v:i for i,v in enumerate(sorted(d))};permutation=[rank[v] for v in d];seen=set();cycles=0
  for i in range(n):
   if i in seen:continue
   cycles+=1
   while i not in seen:seen.add(i);i=permutation[i]
  if not x or x[0]!=cycles:return False
  offset=1;used=set();result=d[:]
  for _ in range(cycles):
   size=x[offset];offset+=1;indices=x[offset:offset+size];offset+=size
   if size<=0 or len(indices)!=size or any(not 1<=i<=n or i in used for i in indices) or len(set(indices))!=size:return False
   used.update(indices)
   for i,v in zip(sorted(indices),sorted(d[j-1] for j in indices)):result[i-1]=v
  return offset==len(x) and len(used)==n and result==sorted(d)
 if tid=='taco_0220':
  n,values=d
  if len(x)!=2*n+1 or x[1:].count(1)!=n or x[1:].count(2)!=n:return False
  counts=collections.Counter(values);total=len(counts)+sum(count>=2 for count in counts.values());optimum=(total//2)*((total+1)//2)
  actual=len({v for v,group in zip(values,x[1:]) if group==1})*len({v for v,group in zip(values,x[1:]) if group==2})
  return x[0]==actual==optimum
 if tid=='taco_0308':
  n,e1,e2=d;expected=n-1-max(len(e1),len(e2))
  if not x or x[0]!=expected or len(x)!=1+2*expected:return False
  ds1,ds2=DSU(n),DSU(n)
  for u,v in e1:ds1.join(u-1,v-1)
  for u,v in e2:ds2.join(u-1,v-1)
  for u,v in zip(x[1::2],x[2::2]):
   if not (1<=u<=n and 1<=v<=n and ds1.join(u-1,v-1) and ds2.join(u-1,v-1)):return False
  return True
 if tid=='taco_0984':
  if len(x)!=2*len(d):return False
  grid=[[False]*4 for _ in range(4)]
  for tile,r,c in zip(d,x[::2],x[1::2]):
   r-=1;c-=1;cells=[(r,c),(r+1,c)] if tile=='0' else [(r,c),(r,c+1)]
   if any(not (0<=rr<4 and 0<=cc<4) or grid[rr][cc] for rr,cc in cells):return False
   for rr,cc in cells:grid[rr][cc]=True
   rows=[i for i in range(4) if all(grid[i])];cols=[j for j in range(4) if all(grid[i][j] for i in range(4))]
   for i in rows:grid[i]=[False]*4
   for j in cols:
    for i in range(4):grid[i][j]=False
  return True
 raise KeyError(tid)
