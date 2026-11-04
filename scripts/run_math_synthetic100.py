"""Hand-designed synthetic distributions; real failures; unmodified autonomous T/F runner."""
import json,random,itertools,math,time,urllib.request,sys
from functools import lru_cache
from fractions import Fraction
from pathlib import Path
import run_math_auto100 as base
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.contracts import fingerprint
from failure_evo.autonomous_mvp import FrozenLinuxBackend
OUT=ROOT/'runs/math_synthetic100_20261031_01'

def expression(p):
 nums,ops=p['numbers'],p['operations']
 def op(a,b,o):return a+b if o=='+' else a-b if o=='-' else a*b
 @lru_cache(None)
 def dp(i,j):
  if j-i==1:return frozenset([nums[i]])
  return frozenset(op(a,b,ops[k-1]) for k in range(i+1,j) for a in dp(i,k) for b in dp(k,j))
 def trees(i,j):
  if j-i==1:return [nums[i]]
  return [op(a,b,ops[k-1]) for k in range(i+1,j) for a in trees(i,k) for b in trees(k,j)]
 a=set(dp(0,len(nums)));b=set(trees(0,len(nums)));assert a==b
 return str(len(a)),dict(oracle1='interval value sets',oracle2='all full binary tree evaluations',agreement=True,trees=len(trees(0,len(nums))))
def prime(n):
 if n<2:return False
 return all(n%d for d in range(2,math.isqrt(n)+1))
def digits(p):
 ds=p['digits'];n=p['length'];repeat=p['repetition_allowed']
 vals=[]
 for t in itertools.product(ds,repeat=n):
  if t[0]==0 or not repeat and len(set(t))<n:continue
  x=int(''.join(map(str,t)))
  if prime(x):vals.append(x)
 # Different domain enumeration and sieve reference, not candidate output.
 stop=10**n;sieve=bytearray(b'\x01')*stop;sieve[:2]=b'\x00\x00'
 for d in range(2,math.isqrt(stop-1)+1):
  if sieve[d]:sieve[d*d:stop:d]=b'\x00'*len(range(d*d,stop,d))
 allowed=set(map(str,ds));b=[]
 for x in range(10**(n-1),stop):
  s=str(x)
  if sieve[x] and set(s)<=allowed and (repeat or len(set(s))==n):b.append(x)
 assert set(vals)==set(b)
 return str(len(vals)),dict(oracle1='digit tuples plus trial division',oracle2='integer scan plus Eratosthenes sieve',agreement=True)
def walk(p):
 steps=p['steps'];target=p['target'];n=p['time'];m=len(steps)
 states={0:Fraction(1)};hit=Fraction(int(target==0 and n==0))
 if target==0:states={}
 for t in range(1,n+1):
  new={};hit=Fraction(0)
  for x,q in states.items():
   for d in steps:
    y=x+d
    if y==target:hit+=q/m
    else:new[y]=new.get(y,Fraction(0))+q/m
  states=new
 # Count surviving words, difference at final step yields first-hit count.
 counts={} if target==0 else {0:1};before=0
 for t in range(1,n+1):
  before=sum(counts.values());nexts={}
  for x,q in counts.items():
   for d in steps:
    if x+d!=target:nexts[x+d]=nexts.get(x+d,0)+q
  counts=nexts
 b=Fraction(int(target==0)) if n==0 else Fraction(before*m-sum(counts.values()),m**n)
 assert hit==b
 return str(hit),dict(oracle1='absorbed rational probability propagation',oracle2='integer surviving-word count difference',agreement=True)

def statement(f,p):
 block=json.dumps(p,separators=(',',':'))
 if f=='expression':s='The ordered numbers and intervening operations are listed below. Insert parentheses to form any full binary parenthesization, keeping every number and operation in its given order and using each exactly once. All arithmetic is over the integers. Count distinct resulting numerical values, not distinct parenthesizations. There is no other precedence once the full parentheses are chosen.'
 elif f=='digits':s='Count prime positive integers in base ten of exactly the specified length, using only digits from the given set. A leading zero is forbidden. If repetition_allowed is true, a digit may be reused any number of times; if false, each digit may occur at most once. Count distinct integers.'
 else:s='A walk starts at position 0 at time 0. At each step independently, choose uniformly one entry from steps and add it to the current position. What is the probability that the first visit to target occurs exactly at time? A visit at time 0 counts as the first visit. Give an exact rational probability.'
 return s+'\nInput data: '+block

def freeze():
 if OUT.exists():raise RuntimeError('new run only')
 rng=random.Random(73120261031);tasks=[];private=[];reviews=[];seen=set()
 for i in range(100):
  f=['expression','digits','walk'][i%3]
  while True:
   if f=='expression':
    n=rng.choice([7,8,9]);p=dict(numbers=[rng.randint(2,19) for _ in range(n)],operations=[rng.choice(['+','-','*']) for _ in range(n-1)])
   elif f=='digits':p=dict(digits=sorted(rng.sample(range(10),rng.choice([5,6,7]))),length=rng.choice([3,4]),repetition_allowed=bool(rng.randrange(2)))
   else:p=dict(steps=rng.choice([[-1,1],[-2,1],[-2,-1,1,2],[-1,1,2]]),target=rng.choice([-3,-2,-1,1,2,3]),time=rng.randint(12,20))
   key=fingerprint([f,p])
   if key not in seen:seen.add(key);break
  answer,review={'expression':expression,'digits':digits,'walk':walk}[f](p)
  t=dict(task_id=f'synthetic100-{i:03d}',problem=statement(f,p));tasks.append(t);private.append(dict(task_id=t['task_id'],gold_answer=answer,problem_sha256=fingerprint(t['problem']),family=f,parameters=p));reviews.append(dict(task_id=t['task_id'],**review))
 roles=dict(Discovery=tasks[:20],Design=tasks[20:30],Gate=tasks[30:40],Test=tasks[40:])
 files=[Path(__file__).resolve(),ROOT/'scripts/run_math_auto100.py',ROOT/'scripts/run_math_v3_development.py']+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))
 p=dict(version='synthetic-failure-learning100-v1',model='deepseek-flash',seed=73120261031,tasks_total=100,roles={k:len(v) for k,v in roles.items()},roles_hash=fingerprint(roles),private_hash=fingerprint(private),max_calls=404,max_usd=20,solver=dict(calls=2,output=4096,input_upper=32768,temperature=0,profile='concise-v1'),generation=dict(arms=['T','F'],one_hypothesis_each=True,max_candidates_each=1,revisions=0,calls_each=2,output=8192,input_upper=65536,source_selection='earliest6finalCONFIRMED_WRONG, shared source questions T/F'),worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),source_hashes={str(f.relative_to(ROOT)):sha(f) for f in files},manual_design='Task distributions and independent references only; no error fabrication; no candidate algorithm supplied; no old operator code',admission='unchanged existing MathLearningPipeline source+Design useful and refusal controls then Gate useful; reject any incorrect applied output/error; >=1correct applied required each role',comparison='60 paired held-out parameter instances, same real solver; no revision after evaluation',scope='hand-designed synthetic mechanisms; parameter transfer within3families, NOT100independentoriginalMATHproblems; one generated operator sample/arm; no universal causal claim',stops=['UNKNOWN/pending','Worker or permission/data failure','budget cap'],authorization='User requests hand-designed real automatic learning benefit experiment, continuing100-task scale; new bounded20USD cap')
 price=urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read();assert b'$0.3' in price and b'$1.2' in price
 save(OUT/'protocol.json',p);save(OUT/'freeze.json',{'sha256':fingerprint(p)});save(OUT/'roles.json',roles);save(OUT/'tasks.json',tasks);save(OUT/'private.json',private);save(OUT/'oracle_acceptance.json',reviews);(OUT/'pricing.html').write_bytes(price)
 for f in files:
  q=OUT/'frozen_source'/f.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(f.read_bytes())
 print('FROZEN',fingerprint(p),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='freeze':freeze()
 else:base.OUT=OUT;base.run()
