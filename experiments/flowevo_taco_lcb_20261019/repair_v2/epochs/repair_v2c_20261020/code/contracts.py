"""Input contracts are separate from candidate correctness. No index-only exclusions."""
import ast
import collections
import json
import math
import re
from semantic import Cursor, InvalidTest, SUPPORTED, parse, require

# First line T; each case: n then n integers, with task-specific ranges below.
ARRAY_TASKS = set('''taco_0003 taco_0078 taco_0279 taco_0401 taco_0861 taco_0914 taco_0960
taco_0293'''.split())
VALIDATED = ARRAY_TASKS | set('''taco_0033 taco_0121 taco_0783 taco_0911 taco_0081 taco_0145
taco_0354 taco_0429 taco_0619 taco_0779 taco_0979 taco_0980 taco_0627 taco_0997 taco_0038
taco_0106 taco_0181 taco_0715 taco_0777 taco_0956 taco_0055 taco_0099 taco_0135 taco_0237
taco_0393 taco_0414 taco_0511 taco_0532 taco_0863 taco_0491 taco_0431 taco_0563 taco_0471
taco_0234 taco_0602 taco_0694 taco_0947 taco_0857 lcb_leetcode_3344'''.split()) | SUPPORTED


def std_input(value):
    if isinstance(value, list) and all(isinstance(x,str) for x in value):
        return "\n".join(value)
    require(isinstance(value,str),"stdio test input must be a string or list of lines")
    return value


def function_args(task, value):
    if task['dataset']=='taco':
        require(isinstance(value,list),"TACO function input must be an argument array")
        return value
    require(isinstance(value,str),"LCB function arguments must be JSON lines")
    try:return [json.loads(line) for line in value.split('\n')]
    except (ValueError,TypeError) as exc:raise InvalidTest("malformed JSON-line function arguments") from exc


def expected_value(task,value):
    if not task.get('function_name'):
        return std_input(value)
    if task['dataset']=='taco':
        require(isinstance(value,list) and len(value)==1,"TACO function result must have one declared return envelope")
        return value[0]
    try:return json.loads(value)
    except (ValueError,TypeError) as exc:raise InvalidTest("malformed reference JSON") from exc


def signature_check(task,args):
    source=task.get('starter_code','')
    if not source:return
    try:tree=ast.parse(source)
    except SyntaxError:return
    functions=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==task['function_name']]
    if not functions:return
    f=functions[0];params=[a for a in f.args.args if a.arg not in ('self','cls')]
    require(len(params)-len(f.args.defaults)<=len(args)<=len(params) or f.args.vararg is not None,"argument count differs from declared function signature")
    def matches(value,annotation):
        if isinstance(annotation,ast.Name):
            if annotation.id in ('int','bool','str','float'):
                typ={'int':int,'bool':bool,'str':str,'float':(int,float)}[annotation.id]
                return isinstance(value,typ) and not (annotation.id=='int' and isinstance(value,bool))
        if isinstance(annotation,ast.Subscript) and isinstance(annotation.value,ast.Name) and annotation.value.id in ('List','list'):
            return isinstance(value,list) and all(matches(x,annotation.slice) for x in value)
        return True
    for arg,param in zip(args,params):
        if param.annotation:require(matches(arg,param.annotation),"argument type/shape differs from starter signature")


def count_cases(c, limit=100000):
    n=c.one(); require(1<=n<=limit,"testcase count outside bounds"); return range(n)


def ints_range(a,lo,hi,why='element range'):
    require(all(lo<=x<=hi for x in a),why)


def tree_edges(n,edges):
    require(len(edges)==n-1,'tree requires exactly n-1 edges')
    parents=list(range(n))
    def root(x):
        while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
        return x
    for u,v in edges:
        require(1<=u<=n and 1<=v<=n,'tree vertex range');a,b=root(u-1),root(v-1)
        require(a!=b,'tree cycle or duplicate edge');parents[a]=b


def validate(task,inp):
    tid=task['task_id'];data=None
    if task.get('function_name'):
        args=function_args(task,inp);signature_check(task,args)
        if tid=='lcb_leetcode_3344':
            require(len(args)==1 and isinstance(args[0],list) and 3<=len(args[0])<=100000,'points length must be at least 3')
            require(all(isinstance(p,list) and len(p)==2 and all(type(v) is int and 1<=v<=10**8 for v in p) for p in args[0]),'points must have shape n x 2 and positive coordinates')
        if tid=='taco_0694':require(len(args)==1 and type(args[0]) is int and 3<=args[0]<=10**9 and math.isqrt(8*args[0]+1)**2==8*args[0]+1,'n must be triangular and in 3..1e9')
        if tid=='taco_0947':require(len(args)==1 and type(args[0]) is int and args[0]>0 and '0' not in str(args[0]),'digit 0 is explicitly excluded')
        if tid=='taco_0857':require(len(args)==2 and all(type(v) is int for v in args) and 5<=args[0]<=1000 and 1<=args[1]<=10,'c_max/num_sol outside stated range')
        if tid in SUPPORTED:data=parse(tid,inp)
        return data
    text=std_input(inp)
    require(not any(ord(ch)<32 and not ch.isspace() for ch in text),'non-whitespace control character in input')
    if tid in SUPPORTED:return parse(tid,text)
    if tid not in VALIDATED:return None
    c=Cursor(text)
    if tid in ARRAY_TASKS:
        for _ in count_cases(c):
            n=c.one();require(n>=1,'array length');a=c.take(n)
            if tid=='taco_0960':require(sorted(a)==list(range(1,n+1)),'not a permutation')
            elif tid=='taco_0078':ints_range(a,0,100)
            elif tid=='taco_0401':ints_range(a,0,n-1)
            else:ints_range(a,1,10**9)
    elif tid=='taco_0033':
        for _ in count_cases(c):
            n,q=c.take(2);s=c.take(1,False)[0];require(n>0 and q>0 and len(s)==n and bool(re.fullmatch('[a-z]+',s)),'S length/alphabet');ints_range(c.take(q),0,10**9)
    elif tid=='taco_0121':
        for _ in count_cases(c):
            n,k=c.take(2);require(1<=k<=n,'K bounds');ints_range(c.take(n),1,n)
    elif tid=='taco_0783':
        for _ in count_cases(c):require(bool(re.fullmatch('[123]+',c.take(1,False)[0])),'string alphabet must be 1,2,3')
    elif tid=='taco_0911':
        n=c.one();s=c.take(1,False)[0];require(n>=2 and len(s)==2*n-2,'key/door string length');require(all(ch.isascii() and (ch.islower() if i%2==0 else ch.isupper()) for i,ch in enumerate(s)),'key/door alphabet')
    elif tid=='taco_0081':
        n,m=c.take(2)
        for _ in range(n):k=c.one();ints_range(c.take(k),1,m)
    elif tid=='taco_0145':require(1<=c.one()<=10000,'n outside 1..10000')
    elif tid=='taco_0354':
        for _ in count_cases(c):
            n,q=c.take(2);require(n>=2 and 1<=q<=n,'N,Q bounds');ints_range(c.take(n),1,10**9)
            for _ in range(q):i,v=c.take(2);require(1<=i<=n and 1<=v<=10**9,'update bounds')
    elif tid=='taco_0429':
        for _ in count_cases(c):
            n,q=c.take(2);sizes=[]
            for _ in range(n):k=c.one();require(k>=1,'cycle length');sizes.append(k);ints_range(c.take(k),1,1000)
            for i in range(n):u,v,w=c.take(3);require(1<=u<=sizes[i] and 1<=v<=sizes[(i+1)%n] and 1<=w<=1000,'cycle bridge endpoints/weight')
            for _ in range(q):
                v1,c1,v2,c2=c.take(4);require(1<=c1<=n and 1<=c2<=n and c1!=c2 and 1<=v1<=sizes[c1-1] and 1<=v2<=sizes[c2-1],'cycle query endpoints')
    elif tid=='taco_0619':
        n,m=c.take(2);rows=c.take(n,False);require(n>0 and m>0 and all(len(row)==m and not set(row)-set('.#') for row in rows),'grid dimensions/alphabet')
    elif tid=='taco_0779':
        for _ in count_cases(c):
            n,k=c.take(2);require(n>=2 and 1<=k<=n,'N,K bounds');tree_edges(n,[c.take(2) for _ in range(n-1)])
    elif tid=='taco_0979':
        for _ in count_cases(c):
            n,k,q=c.take(3);s=c.take(1,False)[0];require(1<=k<=n and len(s)==n and not set(s)-{'0','1'},'binary string length/alphabet')
            for _ in range(q):l,r=c.take(2);require(1<=l<=r<=n,'query range')
    elif tid=='taco_0980':
        n,m=c.take(2)
        for size in (n,m):a=c.take(size);require(size>=1 and all(1<=x<=10**10 for x in a) and all(a[i]<a[i+1] for i in range(size-1)),'head/track order or length')
    elif tid=='taco_0627':
        for _ in count_cases(c):
            s=c.one();require(s>=1,'season count');c.take(s)
            for _ in range(s):episodes=c.one();require(episodes>=1,'episode count');c.take(episodes)
    elif tid=='taco_0997':
        for _ in count_cases(c):
            n=c.one();a=c.take(n);require(2<=n<=360 and all(0<=x<360 for x in a) and all(a[i]<a[i+1] for i in range(n-1)),'angle range/uniqueness')
    elif tid=='taco_0038':
        n,k=c.take(2);require(2<=n<=200000 and 1<=k<n,'n,k bounds');tree_edges(n,[c.take(2) for _ in range(n-1)])
    elif tid=='taco_0106':
        for _ in count_cases(c):
            n,m=c.take(2);s,a=c.take(2,False);require(n>=1 and m>=1 and len(s)==n and len(a)==m and not set(s)-set('?abcde') and not set(a)-set('abcde'),'string dimensions/alphabet')
    elif tid=='taco_0181':
        for _ in count_cases(c):
            n,m=c.take(2);require(n>=1 and m>=0,'graph dimensions')
            for _ in range(m):u,v=c.take(2);require(1<=u<=n and 1<=v<=n and u!=v,'graph endpoints')
    elif tid=='taco_0715':
        for _ in count_cases(c):
            n,k=c.take(2);require(n>=2 and n%2==0 and 1<=k<=200000,'N,K bounds');ints_range(c.take(n),1,k)
    elif tid=='taco_0777':
        for _ in count_cases(c):
            n,h=c.take(2);require(1<=h<=n,'cave height')
            for _ in range(n):lo,hi=c.take(2);require(0<=lo<=hi<n,'gap endpoints')
    elif tid=='taco_0956':
        for _ in count_cases(c):
            n=c.one();a,b=c.take(2,False);require(n>0 and len(a)==len(b)==n and not set(a+b)-set('abcdefghijklmnopqrst'),'string dimensions/alphabet a..t')
    elif tid=='taco_0055':
        for _ in count_cases(c):
            n,m=c.take(2);require(n>=1 and m>=1,'monster counts');c.take(n);d1=c.take(1,False)[0];c.take(m);d2=c.take(1,False)[0];require(len(d1)==n and len(d2)==m and not set(d1+d2)-{'A','D'} and 'D' in d2,'monster mode lengths/alphabet/defender')
    elif tid=='taco_0099':
        n,m=c.take(2);a=c.take(n);require(n>=1 and m>=n+1 and all(0<=x<m for x in a) and all(a[i]<a[i+1] for i in range(n-1)),'bag count/order/range')
    elif tid=='taco_0135':
        for _ in count_cases(c):
            n=c.one();ints_range(c.take(n),1,100000);q=c.one()
            for _ in range(q):p,k=c.take(2);require(1<=p<=100000 and 1<=k<=n,'dish query range')
    elif tid=='taco_0237':
        m,n=c.take(2);require(m>=1 and n>=1,'set/vertex count');c.take(m);c.take(n)
        for _ in range(m):size=c.one();row=c.take(size);require(1<=size<=n and len(set(row))==size and all(1<=v<=n for v in row),'set length/range/duplicates')
    elif tid=='taco_0393':
        for _ in count_cases(c):
            n,q=c.take(2);ints_range(c.take(n),1,10**9)
            for _ in range(q):l,r,y=c.take(3);require(1<=l<r<=n and y>=1,'laser query bounds')
    elif tid=='taco_0414':
        for _ in count_cases(c):
            h,k=c.take(2);require(1<=h<=20,'height bounds');c.take(2**h)
    elif tid=='taco_0511':
        for _ in count_cases(c):
            n,k=c.take(2);a=c.take(n);moves=c.take(k);require(1<=k<=min(100,n) and len(set(a))==n and len(set(moves))==k and 1 in moves and all(1<=i<=n for i in moves),'stack/move dimensions or distinctness')
    elif tid=='taco_0532':
        for _ in count_cases(c):
            n,d=c.take(2);a=c.take(n);require(1<=d<=n and sorted(a)==list(range(1,n+1)),'D bounds or invalid permutation')
    elif tid=='taco_0863':
        n,q=c.take(2);rules=[c.take(2,False) for _ in range(q)];require(2<=n<=6 and 1<=q<=36 and len({a for a,b in rules})==q and all(len(a)==2 and len(b)==1 and not set(a+b)-set('abcdef') for a,b in rules),'rule dimensions/alphabet/uniqueness')
    elif tid=='taco_0491':
        for _ in count_cases(c):
            n=c.one();require(1<=n<=100000,'n bounds');ints_range(c.take(n),0,2**30-1);ints_range(c.take(n),0,2**30-1)
    elif tid=='taco_0431':
        n,m=c.take(2);a=c.take(n,False);b=c.take(m,False);require(1<=n<=1000 and 1<=m<=1000 and len(set(a))==n and len(set(b))==m and all(re.fullmatch('[a-z]{1,500}',s) for s in a+b),'word counts/uniqueness/alphabet')
    elif tid=='taco_0563':
        for _ in count_cases(c):
            n,m=c.take(2);grid=c.take(n,False);require(1<=n<=100 and 1<=m<=100 and all(len(r)==m for r in grid),'grid dimensions');require(grid[-1][-1]=='C' and all(ch in 'RD' for i,row in enumerate(grid) for j,ch in enumerate(row) if (i,j)!=(n-1,m-1)),'counter/direction alphabet')
    elif tid=='taco_0471':
        for _ in count_cases(c):
            n=c.one();require(1<=n<=100000,'array size');ints_range(c.take(n),1,10**9)
    elif tid=='taco_0234':
        n,m=c.take(2);require(1<=n<=100000 and 1<=m<=100000,'array/query size');ints_range(c.take(n),1,10**9)
        for _ in range(m):typ,l,r=c.take(3);require(typ in (1,2) and 1<=l<=r<=n,'query bounds')
    elif tid=='taco_0602':
        n=c.one();require(1<=n<=30,'map size');cells=''.join(c.take(n*n,False));require(len(cells)==n*n and cells.count('S')==cells.count('E')==1 and not set(cells)-set('SETP'),'map dimensions/alphabet')
    c.end();return data


def reference_oracle(task,inp):
    """Only independent proved oracles; None means no replacement claim."""
    tid=task['task_id']
    if tid=='taco_0471':
        c=Cursor(std_input(inp));answers=[]
        for _ in count_cases(c):
            n=c.one();counts=collections.Counter(x.bit_length() for x in c.take(n));answers.append(str(sum(n*(n-1)//2 for n in counts.values())))
        return '\n'.join(answers),'same highest set bit iff XOR < AND'
    if tid=='taco_0602':
        tokens=std_input(inp).split();n=int(tokens[0]);grid=''.join(tokens[1:]);start=grid.index('S');end=grid.index('E');q=collections.deque([start]);dist={start:0}
        while q:
            u=q.popleft();r,c=divmod(u,n)
            for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                rr,cc=r+dr,c+dc;v=rr*n+cc
                if 0<=rr<n and 0<=cc<n and grid[v]!='T' and v not in dist:dist[v]=dist[u]+1;q.append(v)
        return str(dist.get(end,-1)),'independent BFS on four-neighbor obstacle grid'
    if tid=='taco_0234':
        c=Cursor(std_input(inp));n,m=c.take(2)
        if n*m>100000:return None
        a=c.take(n)
        for _ in range(m):
            typ,l,r=c.take(3);segment=a[l-1:r];rest=a[:l-1]+a[r:];a=segment+rest if typ==1 else rest+segment
        return str(abs(a[0]-a[-1]))+'\n'+' '.join(map(str,a)),'independent direct list simulation (n*m <= 100000)'
    return None
