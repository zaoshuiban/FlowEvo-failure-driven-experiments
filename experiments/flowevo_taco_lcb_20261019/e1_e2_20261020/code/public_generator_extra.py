"""Second preregistered public search batch, no hidden test access. Seed20261021.
Extends coverage to graph paths/MST, range updates, dish rotations, monster minimax,
family forests and series partial fractions. Generation occurs before E2 selection.
"""
import collections,functools,itertools,json,math,pathlib,random,hashlib
from fractions import Fraction
R=random.Random(20261021)
def tests():
 out=collections.defaultdict(list)
 def add(t,inp,exp,proof,ci=False):out['taco_'+t].append({'input':inp,'expected':str(exp),'oracle':proof,'case_insensitive':ci,'provenance':'statement-domain public generator extra; no hidden inputs'})
 def batch(t,rows,proof,limit=10):
  for i in range(0,len(rows),limit):
   a=rows[i:i+limit];add(t,str(len(a))+'\n'+'\n'.join(x[0] for x in a),'\n'.join(str(x[1]) for x in a),proof)
 rows=[]
 for _ in range(180):
  n=R.randrange(1,4);m=R.randrange(1,4);v=[R.randrange(1,9) for i in range(n+m)];s=tuple(R.choice('AD') for i in v)
  @functools.lru_cache(None)
  def f(state,turn):
   score=sum(v[i] for i in range(n) if state[i]!='X')-sum(v[i] for i in range(n,n+m) if state[i]!='X');vals=[score]
   own=range(n) if turn==0 else range(n,n+m);opp=range(n,n+m) if turn==0 else range(n)
   for i in own:
    if state[i]!='A':continue
    for j in opp:
     if state[j]!='D':continue
     b=list(state);b[i]='D';b[j]='X';vals.append(f(tuple(b),turn^1))
   return (max if turn==0 else min)(vals)
  val=f(s,0);rows.append((f'{n} {m}\n'+' '.join(map(str,v[:n]))+'\n'+''.join(s[:n])+'\n'+' '.join(map(str,v[n:]))+'\n'+''.join(s[n:]),val))
 batch('0055',rows,'Full minimax: include stopping and every legal attacker/defender choice.',10)
 rows=[]
 for _ in range(100):
  n=R.randrange(1,5);a=[R.randrange(n) for i in range(n)];best=0
  for parent in itertools.product(range(-1,n),repeat=n):
   valid=True
   for i in range(n):
    cur=i;seen=set()
    while cur!=-1:
     if cur in seen:valid=False;break
     seen.add(cur);cur=parent[cur]
    if not valid:break
   if valid:best=max(best,sum(parent.count(i)==a[i] for i in range(n)))
  rows.append((str(n)+'\n'+' '.join(map(str,a)),best))
 batch('0401',rows,'Enumerate every directed parent forest and count exactly truthful claims.',100)
 rows=[]
 for _ in range(130):
  n=R.randrange(1,5);dishes=[[R.randrange(1,8) for i in range(R.randrange(1,5))] for j in range(n)];best=0
  for shifts in itertools.product(*(range(len(x)) for x in dishes)):
   rot=[x[k:]+x[:k] for x,k in zip(dishes,shifts)];best=max(best,sum(abs(rot[i][-1]-rot[i+1][0])*(i+1) for i in range(n-1)))
  rows.append((str(n)+'\n'+'\n'.join(str(len(x))+' '+' '.join(map(str,x)) for x in dishes),best))
 batch('0657',rows,'Enumerate all combinations of cyclic rotations and compute the objective directly.',10)
 for _ in range(100):
  n=R.randrange(1,9);a=[R.randrange(1,40) for i in range(n)];initial=a[:];qs=[]
  for j in range(15):
   if R.randrange(2):
    l=R.randrange(n);r=R.randrange(l,n);p=R.choice([2,3,5]);qs.append(f'1 {l+1} {r+1} {p}')
    for i in range(l,r+1):
     if a[i]%p==0:a[i]//=p
   else:
    i=R.randrange(n);d=R.randrange(1,40);qs.append(f'2 {i+1} {d}');a[i]=d
  add('0395',str(n)+'\n'+' '.join(map(str,initial))+'\n'+str(len(qs))+'\n'+'\n'.join(qs),' '.join(map(str,a)),'Direct list simulation of all updates.')
 for _ in range(90):
  n=R.randrange(1,8);a=[R.randrange(1,20) for i in range(n)];edges=[(i,R.randrange(i)) for i in range(1,n)];adj=[[] for i in range(n)]
  for u,v in edges:adj[u].append(v);adj[v].append(u)
  best=0
  for start in range(n):
   queue=[(start,-1,a[start],1)]
   for u,p,g,dist in queue:
    if g>1:best=max(best,dist)
    for v in adj[u]:
     if v!=p:queue.append((v,u,math.gcd(g,a[v]),dist+1))
  add('0118',str(n)+'\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges),best,'Enumerate every tree path and calculate its GCD explicitly.')
 for _ in range(90):
  n=R.randrange(2,6);allpairs=list(itertools.combinations(range(n),2));tree=[(i,R.randrange(i)) for i in range(1,n)];pairs=set(tuple(sorted(x)) for x in tree)
  for e in allpairs:
   if R.randrange(2):pairs.add(e)
  edges=[(*e,R.randrange(1,15)) for e in sorted(pairs)];ans=[10**9]*len(edges)
  for subset in itertools.combinations(range(len(edges)),n-1):
   reach={0}
   for i in range(n):
    for e in subset:
     u,v,w=edges[e]
     if u in reach or v in reach:reach.update([u,v])
   if len(reach)==n:
    weight=sum(edges[e][2] for e in subset)
    for e in subset:ans[e]=min(ans[e],weight)
  add('0049',f'{n} {len(edges)}\n'+'\n'.join(f'{u+1} {v+1} {w}' for u,v,w in edges),'\n'.join(map(str,ans)),'Enumerate every n-1 edge subset; independently test connectivity and forced-edge minimum.')
 for _ in range(80):
  m=R.randrange(2,7);a=R.sample(range(10),m);b=[R.randrange(10) for i in range(m-1)];answer=Fraction(0)
  for x in a:
   value=sum(Fraction(b[i])*(-x)**i for i in range(m-1));den=math.prod(y-x for y in a if y!=x);residue=value/den;h=sum((Fraction(1,k) for k in range(1,x+1)),Fraction(0));answer-=residue*h
  mod=1000000007;v=answer.numerator*pow(answer.denominator,-1,mod)%mod
  add('0524',str(m)+'\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b)),v,'Exact rational partial fractions: residue P(-a_i)/product(a_j-a_i), sum=-sum(residue_i*H_a_i).')
 return dict(out)
if __name__=='__main__':
 root=pathlib.Path(__file__).resolve().parents[1];payload=json.dumps({'seed':20261021,'hidden_access':False,'tests':tests()},indent=2)+'\n';p=root/'public_tests_extra_frozen.json'
 if p.exists():assert p.read_text()==payload
 else:p.write_text(payload)
 print({k:len(v) for k,v in json.loads(payload)['tests'].items()})
