"""Independent host-only references; no generated source is evaluated here."""
import ast,re,math
from v4_test_data import walk_answer,polynomial_oracle,ast_value,render,CARDINAL

def reference(family,p):
 try:
  if family=='expression':
   if set(p)-{'expression','base','allow_implicit_multiplication'}:return None
   expr=p['expression'];base=p.get('base',10);implicit=p.get('allow_implicit_multiplication',True)
   if not isinstance(expr,str) or len(expr)>3000 or type(base)!=int or not 2<=base<=36 or type(implicit)!=bool:return None
   if not re.fullmatch(r'[a-zA-Z0-9+*()\s]+',expr):return None
   tokens=re.findall(r'[a-zA-Z0-9]+|[+*()]',expr);out=[];prev=None
   for token in tokens:
    numeric=token not in ('+','*','(',')');curr='n' if numeric else token
    if prev in ('n',')') and curr in ('n','('):
     if not implicit:return None
     out.append('*')
    out.append(str(int(token,base)) if numeric else token);prev=curr
   tree=ast.parse(''.join(out),mode='eval')
   def calc(n):
    if isinstance(n,ast.Constant) and type(n.value)==int:return n.value
    if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Mult)):
     a,b=calc(n.left),calc(n.right);return a+b if isinstance(n.op,ast.Add) else a*b
    raise ValueError('unsupported grammar')
   return str(calc(tree.body))
  if family=='walk':
   if set(p)!={'target_x','target_y','max_steps','step_set'}:return None
   if any(type(p[k])!=int for k in ('target_x','target_y','max_steps')) or not 0<=p['max_steps']<=12:return None
   st=p['step_set']
   if not isinstance(st,list) or not 1<=len(st)<=5 or any(not isinstance(s,list) or len(s)!=2 or any(type(v)!=int or abs(v)>5 for v in s) for s in st):return None
   if abs(p['target_x'])+abs(p['target_y'])>20:return None
   return walk_answer(p)[0]
  if family=='poly':
   if set(p)-{'plus_inputs','minus_inputs','external_point'}:return None
   a,b=p['plus_inputs'],p['minus_inputs']
   if not isinstance(a,list) or not isinstance(b,list) or not a or not b or len(a+b)>10 or any(type(x)!=int or abs(x)>20 for x in a+b) or len(set(a+b))!=len(a+b):return None
   return polynomial_oracle(a,b)[0]
 except (ValueError,TypeError,KeyError,RecursionError,SyntaxError,OverflowError):return None
 return None

def confirmation():
 import random
 rng=random.Random(4282026);rows=[]
 for i in range(24):
  def tree(d):
   if not d or rng.random()<.2:return rng.randint(2,49)
   return (rng.choice(['+','*']),tree(d-1),tree(d-1))
  t=tree(2+i%4);base=[2,7,10,16][i%4];implicit=i%3==0
  p=dict(expression=render(t,base,implicit),base=base,allow_implicit_multiplication=implicit)
  ans=str(ast_value(t));assert reference('expression',p)==ans
  rows.append(dict(id=f'confirm-expr-{i}',family='expression',parameters=p,expected=ans))
 for i in range(24):
  st=[CARDINAL,[[1,0],[-1,0]],[[0,1],[0,-1],[1,0]],[[1,0],[1,0],[-1,0]]][i%4]
  x,y=(0,0) if i<6 else (rng.randint(-4,4),rng.randint(-4,4))
  p=dict(target_x=x,target_y=y,max_steps=i%9,step_set=st)
  rows.append(dict(id=f'confirm-walk-{i}',family='walk',parameters=p,expected=reference('walk',p)))
 for i in range(24):
  n=2+i%7;offset=i//7-2;nodes=list(range(offset,offset+n));a=nodes[::2];b=nodes[1::2]
  p=dict(plus_inputs=a,minus_inputs=b,external_point=min(nodes)-1)
  rows.append(dict(id=f'confirm-poly-{i}',family='poly',parameters=p,expected=reference('poly',p)))
 assert all(x['expected'] is not None for x in rows)
 return rows
