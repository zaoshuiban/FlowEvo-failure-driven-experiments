import pathlib,json,math,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];p=ROOT/'audit';out={}
def load(tid):return json.loads(json.loads((p/'data/tasks'/(tid+'.json')).read_text())['input_output'])
def save(tid,issues):out[tid]=issues
for tid in ['taco_0038','taco_0491','taco_0431','taco_0863','taco_0563','taco_0471','taco_0234','taco_0602','taco_0594','taco_0694','taco_0947','taco_0857']:
 t=load(tid);issues=[]
 for i,(inp,expected) in enumerate(zip(t['inputs'],t['outputs'])):
  reasons=[]
  try:
   if tid=='taco_0038':
    a=list(map(int,inp.split()));n,k=a[:2]
    if len(a)!=2+2*(n-1):reasons.append('tree must contain exactly n-1 edges')
   elif tid=='taco_0491':
    a=list(map(int,inp.split()));idx=1
    for _ in range(a[0]):
     n=a[idx];idx+=1
     if len(a)<idx+2*n:reasons.append('array lengths shorter than declared n');break
     idx+=2*n
    if idx!=len(a):reasons.append('declared testcases/array lengths do not consume input exactly')
   elif tid=='taco_0431':
    a=inp.split();n,m=map(int,a[:2]);s=a[2:2+n];b=a[2+n:]
    if len(s)!=n or len(b)!=m:reasons.append('word counts differ from n,m')
    if len(set(s))!=len(s) or len(set(b))!=len(b):reasons.append('duplicate word violates unique-word constraint')
   elif tid=='taco_0863':
    a=inp.split();n,q=map(int,a[:2]);rules=a[2:]
    if len(rules)!=2*q:reasons.append('rule count differs from q')
    if any(set(x)-set('abcdef') for x in rules):reasons.append('rule contains letters outside a..f')
    if any(len(x)!= (2 if j%2==0 else 1) for j,x in enumerate(rules)):reasons.append('rule string length contract violated')
   elif tid=='taco_0563':
    a=inp.split();idx=1
    for _ in range(int(a[0])):
     n,m=map(int,a[idx:idx+2]);idx+=2;grid=a[idx:idx+n];idx+=n
     if len(grid)!=n or any(len(row)!=m for row in grid):reasons.append('grid dimensions differ from n,m');break
     if grid[-1][-1]!='C' or any(c not in 'RD' for r,row in enumerate(grid) for cidx,c in enumerate(row) if (r,cidx)!=(n-1,m-1)):reasons.append('counter C missing or direction alphabet contract violated')
   elif tid=='taco_0471':
    a=list(map(int,inp.split()));idx=1;ans=[]
    for _ in range(a[0]):
     n=a[idx];idx+=1;b=a[idx:idx+n];idx+=n;counts=collections.Counter(x.bit_length() for x in b if x>0);ans.append(sum(c*(c-1)//2 for c in counts.values()))
    if idx!=len(a):reasons.append('input length contract violated')
    if ans!=list(map(int,expected.split())):reasons.append('expected output disagrees with proven highest-set-bit pair count')
   elif tid=='taco_0234':
    a=list(map(int,inp.split()));n,m=a[:2]
    if len(a)!=2+n+3*m:reasons.append('query/input length contract violated')
    if n*m<=100000:
     b=a[2:2+n];idx=2+n
     for _ in range(m):
      typ,l,r=a[idx:idx+3];idx+=3;x=b[l-1:r];remain=b[:l-1]+b[r:];b=x+remain if typ==1 else remain+x
     ans=[abs(b[0]-b[-1])]+b
     if ans!=list(map(int,expected.split())):reasons.append('expected output disagrees with direct array-operation simulation')
   elif tid=='taco_0602':
    a=inp.split();n=int(a[0]);g=list(''.join(a[1:]));s=g.index('S');e=g.index('E');lower=abs(s//n-e//n)+abs(s%n-e%n)
    if int(expected)<lower:reasons.append('expected distance smaller than Manhattan lower bound')
   elif tid=='taco_0594':
    a=list(map(int,inp.split()))
    if len(a)!=a[0]+1 or any(not 2<=x<=500 for x in a[1:]):reasons.append('permutation input outside stated constraints')
   elif tid=='taco_0694':
    if not 3<=inp[0]<=10**9:reasons.append('n outside stated 3..1e9 range')
   elif tid=='taco_0947':
    if '0' in str(inp[0]):reasons.append('input includes digit 0 explicitly excluded by statement')
   elif tid=='taco_0857':
    if not 5<=inp[0]<=1000 or not 1<=inp[1]<=10:reasons.append('arguments outside stated constraints')
  except Exception as e:reasons.append('contract parser failed: '+repr(e))
  if reasons:issues.append({'test_index':i,'reasons':reasons,'input_preview':str(inp)[:300],'expected_preview':str(expected)[:300]})
 save(tid,issues)
(ROOT/'contract_findings.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print({k:len(v) for k,v in out.items()})
