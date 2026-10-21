"""Diagnostic counterfactual only. Does not overwrite original verdicts."""
import json,pathlib,subprocess,math,resource
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
t=json.loads(pathlib.Path('/task.json').read_text()); tests=json.loads(t['input_output']);tid=t['task_id']
def check(inp,actual,expected):
 a=actual.split();b=expected.split();v=list(map(int,inp.split())) if tid in {'lcb_atcoder_abc350_c','lcb_atcoder_abc311_c','lcb_atcoder_abc315_e','lcb_atcoder_abc366_g','lcb_atcoder_arc181_c'} else []
 if tid=='lcb_atcoder_abc350_c':
  n=v[0];p=v[1:];x=list(map(int,a));k=x[0]
  if not (0<=k<=n and len(x)==1+2*k):return False
  for i in range(k):
   u,w=x[1+2*i]-1,x[2+2*i]-1
   if not (0<=u<n and 0<=w<n):return False
   p[u],p[w]=p[w],p[u]
  return p==list(range(1,n+1))
 if tid=='lcb_atcoder_abc311_c':
  n=v[0];nxt=v[1:];x=list(map(int,a));k=x[0];cy=x[1:]
  return 1<=k<=n and len(cy)==k and len(set(cy))==k and all(1<=u<=n and nxt[u-1]==cy[(i+1)%k] for i,u in enumerate(cy))
 if tid=='lcb_atcoder_abc315_e':
  n=v[0];idx=1;deps=[]
  for i in range(n):
   k=v[idx];idx+=1;deps.append(v[idx:idx+k]);idx+=k
  needed=set();stack=[1]
  while stack:
   u=stack.pop()
   for d in deps[u-1]:
    if d not in needed:needed.add(d);stack.append(d)
  x=list(map(int,a));pos={u:i for i,u in enumerate(x)}
  return len(x)==len(needed) and set(x)==needed and all(pos[d]<pos[u] for u in x for d in deps[u-1])
 if tid=='lcb_atcoder_abc366_g':
  if a[0].lower()=='no':return b[0].lower()=='no'
  n,m=v[:2];x=list(map(int,a[1:]));z=[0]*n
  if len(x)!=n or not all(1<=w<2**60 for w in x):return False
  for i in range(m):
   u,w=v[2+2*i]-1,v[3+2*i]-1;z[u]^=x[w];z[w]^=x[u]
  return not any(z)
 if tid=='lcb_atcoder_arc181_c':
  n=v[0];p=v[1:1+n];q=v[1+n:];rows=actual.split()
  if len(rows)!=n or any(len(r)!=n or set(r)-{'0','1'} for r in rows):return False
  cols=[''.join(r[j] for r in rows) for j in range(n)]
  return all(rows[p[i]-1]<rows[p[i+1]-1] and cols[q[i]-1]<cols[q[i+1]-1] for i in range(n-1))
 if a==b:return True
 if len(a)!=len(b):return False
 try:return all(math.isfinite(float(x)) and math.isclose(float(x),float(y),rel_tol=1e-9,abs_tol=1e-9) for x,y in zip(a,b))
 except:return False
r={'task_id':tid,'diagnostic_only':True,'tests_total':len(tests['inputs']),'tests_passed':0,'comparison':'tokens; numeric tolerance 1e-9; task semantic validator when implemented'}
for i,(inp,out) in enumerate(zip(tests['inputs'],tests['outputs'])):
 try:
  p=subprocess.run(['/usr/bin/python3','/candidate.py'],input=inp,text=True,capture_output=True,timeout=6)
  if p.returncode:r.update(failed_index=i,error=p.stderr[-1500:]);break
  if not check(inp,p.stdout,out):r.update(failed_index=i,actual=p.stdout[:1500],expected=str(out)[:1500]);break
  r['tests_passed']+=1
 except Exception as e:r.update(failed_index=i,error=repr(e));break
r['passed']=r['tests_passed']==r['tests_total'];print('BENCH_JUDGE='+json.dumps(r),flush=True)
