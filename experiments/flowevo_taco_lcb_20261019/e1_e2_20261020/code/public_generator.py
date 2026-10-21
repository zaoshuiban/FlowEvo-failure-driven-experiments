"""Public tests from statement domains only. No hidden task/test/artifact imports.
Seed fixed before execution. Oracles are small exhaustive games, forests, paths,
permutations, switch assignments, direct simulation or elementary counting.
"""
import collections,functools,itertools,json,math,pathlib,random,hashlib
SEED=20261020
R=random.Random(SEED)
def tests():
 out=collections.defaultdict(list)
 def add(t,inp,expected,proof,insensitive=False):out['taco_'+t].append({'input':inp,'expected':str(expected),'oracle':proof,'case_insensitive':insensitive,'provenance':'statement-domain generator; independent of hidden inputs'})
 def batch(t,rows,proof,limit=10,insensitive=False):
  for i in range(0,len(rows),limit):
   a=rows[i:i+limit];add(t,str(len(a))+'\n'+'\n'.join(x[0] for x in a)+'\n','\n'.join(str(x[1]) for x in a),proof,insensitive)
 @functools.lru_cache(None)
 def nut(a,b):return any(not nut(i,x-i) for x in (a,b) for i in range(1,x))
 batch('0180',[(f'{a} {b}','Tuzik' if nut(a,b) else 'Vanka') for a in range(1,13) for b in range(1,13)],'Exhaustively enumerate every legal eat/split move; recursion strictly decreases nut count.',100)
 @functools.lru_cache(None)
 def game(a):
  if a[0]==0:return False
  for i in range(1,len(a)):
   b=list(a);b[0]-=1;b[0],b[i]=b[i],b[0]
   if not game(tuple(b)):return True
  return False
 batch('0130',[(str(len(a))+'\n'+' '.join(map(str,a)),'Alice' if game(a) else 'Bob') for n in range(2,5) for a in itertools.product(range(1,4),repeat=n)],'Exhaustive minimax over legal decrements and swaps.',100,True)
 def lis(a):
  dp=[1]*len(a)
  for i in range(len(a)):
   dp[i]=1+max([dp[j] for j in range(i) if a[j]<a[i]] or [0])
  return max(dp)
 rows=[]
 for n in range(1,7):
  for a in list(itertools.combinations_with_replacement(range(1,4),n)):
   val=max(min(lis(p),lis(p[::-1])) for p in set(itertools.permutations(a)))
   rows.append((str(n)+'\n'+' '.join(map(str,a)),val))
 batch('0914',rows,'Enumerate all distinct rearrangements; quadratic strict LIS in each direction.',100)
 rows=[]
 for _ in range(150):
  n=R.randrange(1,7);a=[R.randrange(8) for i in range(n)];b=[R.randrange(8) for i in range(n)]
  values=[]
  for p in itertools.permutations(b):
   v=(1<<30)-1
   for x,y in zip(a,p):v&=x^y
   values.append(v)
  rows.append((f'{n}\n'+ ' '.join(map(str,a))+'\n'+' '.join(map(str,b)),max(values)))
 batch('0491',rows,'Enumerate every permutation of b and directly compute AND of XORs.',100)
 batch('0294',[(f'{a} {b}','YES' if all((a*a-b*b)%d for d in range(2,math.isqrt(a*a-b*b)+1)) else 'NO') for a in range(2,18) for b in range(1,a)],'Trial divide the actual remaining area a^2-b^2.',5,True)
 rows=[]
 for _ in range(140):
  n=R.randrange(1,9);a=R.randrange(1,n+1);b=R.randrange(1,n+1);xs=[R.randrange(1,n+1) for i in range(n)]
  v=sum(x==a and y==b for x in xs for y in xs)/(n*n)
  rows.append((f'{n} {a} {b}\n'+' '.join(map(str,xs)),f'{v:.10f}'))
 batch('0967',rows,'Enumerate the N^2 equally likely ordered die-face outcomes.',70)
 def palpal(s):
  @functools.lru_cache(None)
  def f(i):return i==len(s) or any(s[i:j]==s[i:j][::-1] and f(j) for j in range(i+2,len(s)+1))
  return f(0)
 rows=[]
 for n in range(1,8):
  for a in itertools.combinations_with_replacement('abc',n):
   rows.append((''.join(a),'YES' if any(palpal(''.join(p)) for p in set(itertools.permutations(a))) else 'NO'))
 batch('0962',rows,'Enumerate every distinct rearrangement and every partition into palindromes of length >=2.',100,True)
 rows=[]
 for _ in range(150):
  n=R.randrange(1,5);m=R.randrange(n,9);q=list(range(1,n+1))+[R.randrange(1,n+1) for i in range(m-n)];R.shuffle(q)
  v=min(i+j for i in range(m+1) for j in range(m-i+1) if set(q[:i]+(q[m-j:] if j else []))==set(range(1,n+1)))
  rows.append((f'{n} {m}\n'+' '.join(map(str,q)),v))
 batch('0812',rows,'Enumerate every non-overlapping popped prefix and suffix.',10)
 rows=[]
 for _ in range(120):
  n=R.randrange(1,5);init=R.randrange(-3,4);time=0;cur={init};lines=[]
  for i in range(n):
   time+=R.randrange(0,4);lo=R.randrange(-5,5);hi=lo+R.randrange(0,5);lines.append((time,lo,hi))
  prev=0
  for t,l,h in lines:cur={x+d for x in cur for d in range(-(t-prev),t-prev+1) if l<=x+d<=h};prev=t
  rows.append((f'{n} {init}\n'+'\n'.join(' '.join(map(str,x)) for x in lines),'YES' if cur else 'NO'))
 batch('0583',rows,'Enumerate all reachable integer temperatures at each reservation time.',100,True)
 for _ in range(80):
  n=R.randrange(2,10);par=[R.randrange(1,i) for i in range(2,n+1)];adj=[[] for i in range(n+1)]
  for i,p in enumerate(par,2):adj[i].append(p);adj[p].append(i)
  todo=[(1,[1])];ans=None
  for u,path in todo:
   if u==n:ans=path;break
   for v in adj[u]:
    if v not in path:todo.append((v,path+[v]))
  add('0363',str(n)+'\n'+' '.join(map(str,par))+'\n',' '.join(map(str,ans)),'BFS enumerates simple paths on the generated rooted tree.')
 for _ in range(80):
  n=R.randrange(1,9);groups=[R.sample(range(1,n+1),R.randrange(n+1)) for i in range(R.randrange(1,7))];reach=[{i} for i in range(1,n+1)]
  changed=True
  while changed:
   changed=False
   for g in groups:
    if not g:continue
    union=set().union(*(reach[i-1] for i in g))
    for i in union:
     if reach[i-1]!=union:reach[i-1]=union.copy();changed=True
  add('0749',f'{n} {len(groups)}\n'+'\n'.join(str(len(g))+' '+ ' '.join(map(str,g)) for g in groups)+'\n',' '.join(str(len(x)) for x in reach),'Explicit repeated news propagation to a fixed point.')
 for _ in range(80):
  n=R.randrange(3,8);edges=[(i,j) for i in range(1,n+1) for j in range(i+1,n+1) if R.randrange(2)];e={tuple(sorted(x)) for x in edges}
  good=all(not (tuple(sorted((x,y))) in e and tuple(sorted((y,z))) in e) or tuple(sorted((x,z))) in e for x,y,z in itertools.permutations(range(1,n+1),3))
  add('0910',f'{n} {len(edges)}\n'+'\n'.join(f'{u} {v}' for u,v in edges)+'\n','YES' if good else 'NO','Directly check every ordered triple against the statement implication.',True)
 for _ in range(65):
  n=R.randrange(2,7);m=R.randrange(2,7);pairs=[R.sample(range(m),2) for i in range(n)];status=[R.randrange(2) for i in range(n)];sw=[[i+1 for i,p in enumerate(pairs) if j in p] for j in range(m)]
  good=any(all((status[i]^bits[a]^bits[b])==1 for i,(a,b) in enumerate(pairs)) for bits in itertools.product(range(2),repeat=m))
  add('0725',f'{n} {m}\n'+' '.join(map(str,status))+'\n'+'\n'.join(str(len(x))+' '+' '.join(map(str,x)) for x in sw)+'\n','YES' if good else 'NO','Enumerate all 2^m switch configurations.')
 # Polygon: enumerate reachable bitboards by simulating actual cannon shots, n<=3.
 rows=[]
 for n in range(1,4):
  seen={0};todo=[0]
  for b in todo:
   for axis in range(2):
    for v in range(n):
     cells=[(v*n+j if axis==0 else j*n+v) for j in range(n)];empty=[]
     for cell in cells:
      if b>>cell&1:break
      empty.append(cell)
     if empty:
      nxt=b|(1<<empty[-1])
      if nxt not in seen:seen.add(nxt);todo.append(nxt)
  for b in range(1<<(n*n)):
   grid='\n'.join(''.join(str(b>>(i*n+j)&1) for j in range(n)) for i in range(n));rows.append((str(n)+'\n'+grid,'YES' if b in seen else 'NO'))
 batch('0337',rows,'Enumerate all states reachable by literal row/column cannon shooting.',500,True)
 rows=[]
 for _ in range(80):
  n=R.randrange(1,10);a=[R.randrange(1,30) for i in range(n)];qs=[];vals=[]
  for j in range(5):
   l=R.randrange(n);r=R.randrange(l,n);v=a[l]
   for x in a[l+1:r+1]:v&=x
   qs.append(f'{l+1} {r+1}');vals.append('ODD' if v%2 else 'EVEN')
  rows.append((str(n)+'\n'+' '.join(map(str,a))+'\n5\n'+'\n'.join(qs),'\n'.join(vals)))
 batch('0900',rows,'Directly AND all elements in each generated legal interval.',10)
 return dict(out)
if __name__=='__main__':
 root=pathlib.Path(__file__).resolve().parents[1];payload=json.dumps({'seed':SEED,'hidden_access':False,'tests':tests()},indent=2)+'\n';p=root/'public_tests_frozen.json'
 if p.exists():assert p.read_text()==payload
 else:p.write_text(payload)
 (root/'public_tests_frozen.sha256').write_text(hashlib.sha256(payload.encode()).hexdigest()+'\n')
 print({k:len(v) for k,v in json.loads(payload)['tests'].items()})
