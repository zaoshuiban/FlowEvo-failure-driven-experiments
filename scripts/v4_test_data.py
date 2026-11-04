"""Host-only independent references. Never imported by model request builder."""
import random,itertools,math
from fractions import Fraction
SEED=402810
CARDINAL=[[1,0],[-1,0],[0,1],[0,-1]]
def ast_value(node):
 if isinstance(node,int):return node
 op,a,b=node;return ast_value(a)+ast_value(b) if op=='+' else ast_value(a)*ast_value(b)
def numeral(n,base):
 if n==0:return '0'
 s='';chars='0123456789abcdefghijklmnopqrstuvwxyz'
 while n:s=chars[n%base]+s;n//=base
 return s
def render(node,base=10,implicit=False):
 if isinstance(node,int):return numeral(node,base)
 op,a,b=node
 return '('+render(a,base,implicit)+('' if implicit and op=='*' else op)+('('+render(b,base,implicit)+')' if implicit and op=='*' else render(b,base,implicit))+')'
def walk_exhaustive(p):
 steps=p['step_set'];N=p['max_steps'];target=(p['target_x'],p['target_y']);hits=0
 for path in itertools.product(steps,repeat=N):
  x=y=0;hit=target==(0,0)
  for dx,dy in path:
   x+=dx;y+=dy;hit=hit or (x,y)==target
  hits+=hit
 return Fraction(hits,len(steps)**N)
def walk_backward(p):
 # Backward probability recursion, independent of forward absorbing path counts.
 from functools import lru_cache
 target=(p['target_x'],p['target_y']);steps=p['step_set']
 @lru_cache(None)
 def f(x,y,n):
  if (x,y)==target:return Fraction(1)
  if n==0:return Fraction(0)
  return sum((f(x+dx,y+dy,n-1) for dx,dy in steps),Fraction(0))/len(steps)
 return f(0,0,p['max_steps'])
def walk_answer(p):
 prob=walk_backward(p)
 if len(p['step_set'])**p['max_steps']<=65536:assert prob==walk_exhaustive(p)
 return str(prob.numerator+prob.denominator),str(prob)
def make():
 rng=random.Random(SEED);rows=[]
 for i in range(40):
  pair={};base=10;implicit=i%2==0
  if i<10:
   a=rng.randint(2,7);b=rng.randint(1,5);d=i%5;n=b
   for _ in range(d):n=('+',b,('*',a,n))
   node=('*',a,n)
   pair={'T':dict(multiplier=a,addend=b,seed=0,depth=d+1),'F':dict(outer_coefficient=a,inner_constant=b,inner_coefficient=a,depth=d)}
  else:
   base=[2,8,10,16,36][i%5]
   def tree(depth):
    if not depth or rng.random()<.25:return rng.randint(0,30)
    return (rng.choice(['+','*']),tree(depth-1),tree(depth-1))
   node=tree(1+i%5)
  expr=render(node,base,implicit);p=dict(expression=expr,base=base,allow_implicit_multiplication=implicit)
  rows.append(dict(id=f'expr-{i:02}',family='expression',role='legal',parameters=p,expected=str(ast_value(node)),oracle='generated-AST-direct-evaluation',ast=node,pair_parameters=pair,problem=f'Evaluate the following integer expression in base {base}: {expr}. Juxtaposition {"denotes multiplication" if implicit else "is not permitted"}; multiplication precedes addition. Return the result as a decimal integer.'))
 expression_boundaries=[('0',10,False,'0'),('a+1',16,False,'11'),('z',36,False,'35'),('11*10',2,False,'6'),('2+3*4',10,False,'14'),('(2+3)*4',10,False,'20'),('2(3+4)',10,True,'14'),('('+ '1+'*200+'1)',10,False,'201'),('('*600+'1'+')'*600,10,False,'1'),('1'*100001,2,False,None),('',10,False,None),('2+(3',10,False,None),('3-1',10,False,None),('4/2',10,False,None),('2**3',10,False,None),('x',10,False,None),('2(3)',10,False,None),('2',2,False,None),('1',1,False,None),(123,10,False,None)]
 for i,(expr,base,implicit,expected) in enumerate(expression_boundaries):
  rows.append(dict(id=f'expr-bound-{i:02}',family='expression',role='boundary_legal' if expected is not None else 'unsupported',parameters=dict(expression=expr,base=base,allow_implicit_multiplication=implicit),expected=expected,oracle='independent arithmetic/grammar review',pair_parameters={}))
 sets=[CARDINAL,[[1,0],[-1,0]],[[1,0],[0,1]],[[2,0],[0,2],[-1,-1]],[[0,0],[1,0],[-1,0]]]
 for i in range(40):
  steps=CARDINAL if i<12 else sets[i%len(sets)];tx,ty=rng.randint(-3,3),rng.randint(-3,3)
  if (tx,ty)==(0,0):tx=1
  p=dict(target_x=tx,target_y=ty,max_steps=1+i%7,step_set=steps);expected,prob=walk_answer(p)
  pair={arm:{k:v for k,v in p.items() if k!='step_set'} for arm in ['T','F']} if steps==CARDINAL else {}
  rows.append(dict(id=f'walk-{i:02}',family='walk',role='legal',parameters=p,expected=expected,probability=prob,oracle='finite-path-enumeration+backward-probability',pair_parameters=pair,problem=f'A walk starts at (0,0). At each step it independently chooses uniformly among the listed move options {steps}. Find the probability of visiting ({tx},{ty}) at least once by time {p["max_steps"]}, including time zero. Write this probability in lowest terms m/n and return m+n.'))
 boundaries=[dict(target_x=0,target_y=0,max_steps=n,step_set=CARDINAL) for n in [0,1,2,4]]
 boundaries += [dict(target_x=1,target_y=0,max_steps=0,step_set=CARDINAL),dict(target_x=1,target_y=0,max_steps=4,step_set=[[1,0],[1,0],[-1,0]]),dict(target_x=0,target_y=0,max_steps=3,step_set=[[0,0],[1,0]]),dict(target_x=1,target_y=0,max_steps=1,step_set=[[1,0]]),dict(target_x=3,target_y=3,max_steps=12,step_set=[[1,0],[0,1]]),dict(target_x=1000,target_y=0,max_steps=200,step_set=[[1,0]])]
 for i,p in enumerate(boundaries):
  exp,prob=walk_answer(p);rows.append(dict(id=f'walk-bound-{i:02}',family='walk',role='boundary_legal',parameters=p,expected=exp,probability=prob,oracle='finite-path/backward',pair_parameters={}))
 default=dict(target_x=2,target_y=2,max_steps=6,step_set=CARDINAL)
 invalid=[{},dict(default,max_steps=-1),dict(default,max_steps=True),dict(default,step_set=[]),dict(default,step_set=[[1]]),dict(default,step_set=[[1,False]]),dict(default,max_steps=201),dict(default,target_x=1001),dict(default,step_set=[[101,0]]),dict(default,probabilities=[.1,.2,.3,.4])]
 for i,p in enumerate(invalid):rows.append(dict(id=f'walk-invalid-{i:02}',family='walk',role='unsupported',parameters=p,expected=None,oracle='type/resource/probability semantics',pair_parameters={}))
 assert len(rows)==120
 return rows

def polynomial_oracle(plus,minus):
 # Exact rational interpolation; integral monic vanishing polynomial proves
 # every Z[x] solution has integral remainder. Thus denominator LCM is minimal.
 import sympy as s
 x=s.Symbol('x');poly=s.Poly(s.interpolate([(i,1) for i in plus]+[(i,-1) for i in minus],x),x)
 return str(math.lcm(*[int(c.q) for c in poly.all_coeffs()])),str(poly.as_expr())
