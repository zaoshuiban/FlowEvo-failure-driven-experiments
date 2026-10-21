"""Independent audited final scoring oracles; never imported by prompt generation."""
import collections,itertools,math
from fractions import Fraction

def transform(s,t):
 if s==t:return 0
 g={}
 for a,b in zip(s,t):
  if a in g and g[a]!=b:return -1
  g[a]=b
 if len(set(t))==26:return -1
 edges={a:b for a,b in g.items() if a!=b};indegree=collections.Counter(edges.values());seen=set();extra=0
 for start in edges:
  path=[];where={};u=start
  while u in edges and u not in seen and u not in where:where[u]=len(path);path.append(u);u=edges[u]
  if u in where:
   cycle=path[where[u]:]
   if all(indegree[v]==1 for v in cycle):extra+=1
  seen.update(path)
 return len(edges)+extra

def brute_transform(s,t,alphabet='abcd'):
 if s==t:return 0
 q=collections.deque([(s,0)]);seen={s}
 while q:
  u,d=q.popleft()
  for a in set(u):
   for b in alphabet:
    if a==b:continue
    v=u.replace(a,b)
    if v==t:return d+1
    if v not in seen:seen.add(v);q.append((v,d+1))
 return -1

def magazine(values):
 i=0;t=values[i];i+=1
 if not(1<=t<=10000):raise ValueError('test count')
 answers=[]
 for case in range(t):
  n=values[i];f=values[i+1];i+=2
  # The statement models ordinary two-sided leaves. Odd page counts are excluded
  # from this audited experiment because treatment of the blank last back is unclear.
  if not(2<=n<=2000 and n%2==0 and 0<=f<=n):raise ValueError('page/leaf contract or odd-page ambiguity')
  pages=values[i:i+f];i+=f
  if len(pages)!=f or len(set(pages))!=f or not all(1<=x<=n for x in pages):raise ValueError('missing page numbers')
  torn=values[i];i+=1;leaves=n//2
  if not 0<=torn<=leaves:raise ValueError('torn leaves bounds')
  printed=n*(n+1)//2-sum(pages)
  answers.append(Fraction(printed*(leaves-torn),leaves))
 if i!=len(values):raise ValueError('extra input')
 return answers

def selftest():
 checked=0
 for n in range(1,4):
  words=[''.join(x) for x in itertools.product('abc',repeat=n)]
  for s in words:
   for t in words:
    assert transform(s,t)==brute_transform(s,t),(s,t,transform(s,t),brute_transform(s,t));checked+=1
 # Every physical leaf subset, including hidden page labels, on small books.
 subset_checks=0
 for n in range(2,9,2):
  for missing in [[],[1],list(range(1,n+1))]:
   for torn in range(n//2+1):
    totals=[]
    for removed in itertools.combinations(range(n//2),torn):
     totals.append(sum(p for p in range(1,n+1) if p not in missing and (p-1)//2 not in removed))
    exact=sum(map(Fraction,totals))/len(totals)
    assert magazine([1,n,len(missing),*missing,torn])==[exact];subset_checks+=1
 return {'transform_exhaustive_string_pairs':checked,'magazine_leaf_subset_checks':subset_checks}
if __name__=='__main__':print(selftest())
