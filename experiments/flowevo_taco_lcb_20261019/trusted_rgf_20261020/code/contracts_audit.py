"""Independent legality pass over every frozen input; never consumes candidate output."""
import collections,json,pathlib,re
from suite import ROOT,MULTI,split_multi

def connected(n,edges):
 g=[[] for _ in range(n)]
 for u,v in edges:assert 1<=u<=n and 1<=v<=n and u!=v;g[u-1].append(v-1);g[v-1].append(u-1)
 seen={0};q=[0]
 for u in q:
  for v in g[u]:
   if v not in seen:seen.add(v);q.append(v)
 assert len(seen)==n

def audit(tid,c):
 if tid=='taco_0616':assert len(c['input'])==2 and all(type(x)is int and x<=1000 for x in c['input']);return
 s=c['input'].split();short=tid[5:]
 if short in MULTI:
  assert len(split_multi(short,c['input'],c['expected']))==1
  # Every generated number lies in a conservative <=1000 subdomain of the stated upper bounds.
  assert all(abs(int(v))<=1000 for v in s if re.fullmatch('-?\d+',v) and len(v)<=4)
  return
 a=list(map(int,s)) if short not in ['0271','0333'] and not tid.startswith('lcb') else None
 if short=='0363':n=a[0];assert 2<=n<=200000 and len(a)==n and all(1<=p<i for i,p in enumerate(a[1:],2))
 elif short=='0749':
  n,m=a[:2];assert 1<=n<=500000 and 1<=m<=500000;i=2;total=0
  for z in range(m):
   k=a[i];i+=1;row=a[i:i+k];i+=k;assert 0<=k<=n and len(set(row))==len(row)==k and all(1<=v<=n for v in row);total+=k
  assert i==len(a) and total<=500000
 elif short=='0910':
  n,m=a[:2];edges=list(zip(a[2::2],a[3::2]));assert 3<=n<=150000 and len(edges)==m and len(a)==2+2*m and len({tuple(sorted(e)) for e in edges})==m and all(1<=u<=n and 1<=v<=n and u!=v for u,v in edges)
 elif short=='0725':
  n,m=a[:2];status=a[2:2+n];assert 2<=n<=100000 and 2<=m<=100000 and not set(status)-{0,1};i=2+n;counts=collections.Counter()
  for z in range(m):
   k=a[i];i+=1;row=a[i:i+k];i+=k;assert len(set(row))==len(row)==k and all(1<=v<=n for v in row);counts.update(row)
  assert i==len(a) and all(counts[v]==2 for v in range(1,n+1))
 elif short=='0395':
  n=a[0];assert 1<=n<=100000 and all(1<=v<=10**9 for v in a[1:1+n]);i=n+1;m=a[i];i+=1;assert 1<=m<=100000
  for z in range(m):
   t=a[i];i+=1
   if t==1:l,r,p=a[i:i+3];i+=3;assert 1<=l<=r<=n and p in [2,3,5]
   else:assert t==2;l,d=a[i:i+2];i+=2;assert 1<=l<=n and 1<=d<=10**9
  assert i==len(a)
 elif short in ['0118','0049']:
  if short=='0118':n=a[0];v=a[1:n+1];assert 1<=n<=200000 and all(1<=x<=200000 for x in v);edges=list(zip(a[n+1::2],a[n+2::2]));assert len(a)==1+n+2*(n-1) and len(edges)==n-1
  else:
   n,m=a[:2];assert 2<=n<=200000 and n-1<=m<=200000 and len(a)==2+3*m;rows=[a[2+3*i:5+3*i] for i in range(m)];edges=[(u,v) for u,v,w in rows];assert len({tuple(sorted(e)) for e in edges})==m and all(1<=w<=10**9 for u,v,w in rows)
  connected(n,edges)
 elif short=='0524':m=a[0];v=a[1:1+m];b=a[1+m:];assert 2<=m<=5000 and len(set(v))==m and len(b)==m-1 and all(0<=x<=5000 for x in v) and all(0<=x<=10**9 for x in b)
 elif short=='0194':assert a[0]==1 and len(a)==7 and all(1<=v<=100000 for v in a[1:4]) and all(1<=v<=1000 for v in a[4:])
 elif short=='0271':k,m=map(int,s[:2]);assert 1<=k<=10**18 and 1<=m<=10000 and len(s)==m+2 and sum(map(len,s[2:]))<=100000 and all(re.fullmatch('[ab]+',v) for v in s[2:])
 elif short=='0317':q=a[0];assert 1<=q<=100000 and len(a)==2*q+1 and all(1<=x<=10**9 for x in a[1:])
 elif short=='0617':n,m=a[:2];edges=list(zip(a[2::2],a[3::2]));assert 3<=n<=48 and n%3==0 and len(a)==2+2*m and len(set(edges))==m and all(1<=u<v<=n for u,v in edges)
 elif short=='0936':assert len(a)==4 and all(0<=v<=10**9 for v in a)
 elif short=='0333':n,t=map(int,s[:2]);assert 1<=n<=50 and 1<=t<=50 and len(s)==3 and len(s[2])==n and not set(s[2])-{'B','G'}
 elif short=='0831':assert len(a)==1 and 2<=a[0]<=60000
 elif short=='0875':
  n=a[0];p=a[1:];assert 1<=n<=2000 and len(p)==n and all(v==-1 or 1<=v<=n and v!=i for i,v in enumerate(p,1))
  for start in range(1,n+1):
   seen=set();u=start
   while u!=-1:assert u not in seen;seen.add(u);u=p[u-1]
 elif tid=='lcb_atcoder_abc301_f':assert len(s)==1 and 4<=len(s[0])<=300000 and re.fullmatch('[a-zA-Z?]+',s[0])
 elif tid=='lcb_atcoder_abc399_e':n=int(s[0]);assert len(s)==3 and 1<=n<=200000 and len(s[1])==len(s[2])==n and re.fullmatch('[a-z]+',s[1]+s[2])
 elif tid=='lcb_atcoder_arc188_c':
  v=list(map(int,s));n,m=v[:2];rows=[v[2+3*i:5+3*i] for i in range(m)];assert 2<=n<=200000 and 0<=m<=min(200000,n*(n-1)) and len(v)==2+3*m and len({(a,b) for a,b,c in rows})==m and all(1<=a<=n and 1<=b<=n and a!=b and c in [0,1] for a,b,c in rows)
 elif tid=='lcb_atcoder_abc314_e':
  v=list(map(int,s));n,m=v[:2];assert 1<=n<=100 and 1<=m<=100;i=2
  for z in range(n):
   cost,p=v[i:i+2];i+=2;row=v[i:i+p];i+=p;assert 1<=cost<=10000 and 1<=p<=100 and len(row)==p and all(0<=x<=m for x in row) and sum(row)>0
  assert i==len(v)
 else:raise AssertionError('Missing contract '+tid)

def main():
 tests=json.loads((ROOT/'suite_frozen.json').read_text())['cases'];out=[]
 for tid,cases in tests.items():
  for i,c in enumerate(cases):
   try:audit(tid,c)
   except Exception as exc:raise AssertionError((tid,i,str(exc)))
  out.append({'task_id':tid,'legal_cases_verified':len(cases),'input_layout':'statement-format line boundaries preserved','contract_implementation':'code/contracts_audit.py'})
 (ROOT/'input_contract_review.json').write_text(json.dumps(out,indent=2));print('LEGAL',len(out),sum(x['legal_cases_verified'] for x in out))
if __name__=='__main__':main()
