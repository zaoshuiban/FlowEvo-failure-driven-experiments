"""Task-specific constructive checkers. No answer-order or token-set shortcuts."""
import bisect
import collections
import math
from functools import reduce
from operator import xor
from semantic_extra import EXTRA_SUPPORTED, parse_extra, accepts_extra
from semantic_more import MORE_SUPPORTED, parse_more, accepts_more


class InvalidTest(ValueError):
    pass


def require(ok, why):
    if not ok:
        raise InvalidTest(why)


class Cursor:
    def __init__(self, text):
        self.a = text.split(); self.i = 0
    def take(self, n=1, numeric=True):
        require(n >= 0 and self.i + n <= len(self.a), "declared input length exceeds provided tokens")
        result = self.a[self.i:self.i+n]; self.i += n
        try: return [int(x) for x in result] if numeric else result
        except ValueError as exc: raise InvalidTest("non-integer input") from exc
    def one(self): return self.take()[0]
    def end(self): require(self.i == len(self.a), "extra tokens outside declared input")


SUPPORTED = set('''lcb_atcoder_abc350_c lcb_atcoder_abc311_c lcb_atcoder_abc315_e
lcb_atcoder_arc181_c lcb_atcoder_abc366_g taco_0594 taco_0137 taco_0510 taco_0831
taco_0946 taco_0720 taco_0552 taco_0056 taco_0617 taco_0054 taco_0444 taco_0519
taco_0638 taco_0574 taco_0347 taco_0422 taco_0771 taco_0796 taco_0381 taco_0945'''.split())


def parse(tid, inp):
    if tid in MORE_SUPPORTED:return parse_more(tid,inp)
    if tid in EXTRA_SUPPORTED:return parse_extra(tid,inp)
    if tid == "taco_0796":
        require(isinstance(inp, list) and len(inp) == 1 and isinstance(inp[0], int), "expected one integer argument")
        n = inp[0]; require(n > 0 and n % 4 == 0 and n <= 1000, "not a supported doubly-even magic-square size")
        return n
    c = Cursor(inp)
    if tid in {"taco_0594", "taco_0056", "taco_0422", "taco_0771"}:
        count = c.one(); require(1 <= count <= 10000, "invalid testcase count"); data = c.take(count)
        lo, hi = {"taco_0594": (2,500), "taco_0056": (1,100000), "taco_0422": (2,100), "taco_0771": (2,1000)}[tid]
        require(all(lo <= n <= hi for n in data), "size outside statement bounds")
    elif tid == "taco_0137":
        n,k=c.take(2); a=c.take(n); require(1<=n<=100 and 1<=k<=100 and all(1<=x<=100 for x in a), "pile bounds"); data=(n,k,a)
    elif tid == "taco_0510":
        data=c.one(); require(5<=data<10**9,"cathetus bounds")
    elif tid == "taco_0831":
        data=c.one(); require(2<=data<=10**9,"n bounds")
    elif tid == "taco_0946":
        data=c.take(2); require(1<=data[0]<=data[1]<=10**18,"interval bounds")
    elif tid == "taco_0054":
        data=c.take(2); require(1<=data[1]<data[0]<=10000,"A,B bounds")
    elif tid == "taco_0552":
        n,k=c.take(2); a=c.take(n); require(n>0 and k>=0 and all(x>0 for x in a),"instrument bounds"); data=(n,k,a)
    elif tid == "taco_0720":
        n=c.one(); data=[tuple(c.take(2,False)) for _ in range(n)]; require(n>=1,"rename count")
        # All names non-empty; consistency is checked while constructing rename chains.
    elif tid == "taco_0617":
        n=c.one(); data=c.take(n); require(n>0 and n%3==0 and all(x in (1,2,3) for x in data),"student levels/count")
    elif tid == "taco_0444":
        n=c.one(); data=[c.take(2) for _ in range(n)]; require(n>0 and all(1<=x<=100 and 1<=y<=100 for x,y in data),"x,y bounds")
    elif tid == "taco_0519":
        count=c.one(); data=[]
        for _ in range(count):
            n,k=c.take(2); a=c.take(n); require(1<=n<=200000 and 0<=k<n and all(1<=x<=10**9 for x in a) and all(a[i]<a[i+1] for i in range(n-1)),"point bounds/order"); data.append((n,k,a))
    elif tid == "taco_0638":
        count=c.one(); data=[c.take(2) for _ in range(count)]; require(count>0 and all(1<=n<=300 and 0<=k<=n*n for n,k in data),"grid bounds")
    elif tid == "taco_0574":
        data=c.take(2); require(all(1<=x<=100 for x in data),"table dimensions")
    elif tid == "taco_0347":
        n=c.one(); data=c.take(n); require(n>0 and all(2<=x<=10**7 for x in data),"divisor input bounds")
    elif tid == "taco_0381":
        count=c.one(); data=[]
        for _ in range(count):
            l,r=c.take(2); require(0<=l<=r<2**17,"xor interval bounds"); a=c.take(r-l+1); require(len(set(a))==len(a) and all(0<=x<2**17 for x in a),"xor array bounds/uniqueness"); data.append((l,r,a))
    elif tid == "taco_0945":
        count=c.one(); data=[]
        for _ in range(count):
            n=c.one(); a=[c.take(5) for _ in range(n)]; require(1<=n<=50000 and all(1<=x<=50000 for row in a for x in row) and all(len({row[j] for row in a})==n for j in range(5)),"rank bounds/uniqueness"); data.append(a)
    elif tid in {"lcb_atcoder_abc350_c", "lcb_atcoder_abc311_c", "lcb_atcoder_arc181_c"}:
        n=c.one(); require(n>0,"n bounds"); a=c.take(n)
        if tid=="lcb_atcoder_abc311_c": require(all(1<=x<=n for x in a),"edge target bounds"); data=(n,a)
        else:
            require(sorted(a)==list(range(1,n+1)),"not a permutation")
            if tid.endswith("arc181_c"):
                b=c.take(n);require(sorted(b)==list(range(1,n+1)),"not a permutation");data=(n,a,b)
            else:data=(n,a)
    elif tid == "lcb_atcoder_abc315_e":
        n=c.one(); deps=[]
        for _ in range(n):
            k=c.one(); row=c.take(k);require(all(1<=d<=n for d in row) and len(row)==len(set(row)),"prerequisite bounds/duplicates"); deps.append(row)
        require(n>0,"n bounds");data=deps
    elif tid == "lcb_atcoder_abc366_g":
        n,m=c.take(2); edges=[c.take(2) for _ in range(m)];require(1<=n<=60 and 0<=m<=n*(n-1)//2 and all(1<=u<v<=n for u,v in edges) and len({tuple(x) for x in edges})==m,"graph bounds/simple graph");data=(n,edges)
    else:raise KeyError(tid)
    c.end();return data


def accepts(tid, data, output):
    """Malformed candidate output is WA; malformed input was rejected by parse()."""
    try:
        if tid in MORE_SUPPORTED:return accepts_more(tid,data,output)
        return accepts_extra(tid,data,output) if tid in EXTRA_SUPPORTED else _accepts(tid,data,output)
    except (ValueError,TypeError,IndexError,KeyError,OverflowError):return False


def _accepts(tid,d,out):
    if tid=="taco_0796":
        n=d
        if not isinstance(out,list) or len(out)!=n or any(not isinstance(r,list) or len(r)!=n for r in out):return False
        if any(type(x) is not int for row in out for x in row):return False
        if sorted(x for row in out for x in row)!=list(range(1,n*n+1)):return False
        target=n*(n*n+1)//2
        return all(sum(r)==target for r in out) and all(sum(out[i][j] for i in range(n))==target for j in range(n)) and sum(out[i][i] for i in range(n))==target and sum(out[i][n-1-i] for i in range(n))==target
    a=out.split()
    if tid=="taco_0720":
        chains={}; current={}
        for old,new in d:
            root=current.pop(old,old)
            require(new not in current,"new handle already occupied")
            chains[root]=new;current[new]=root
        k=int(a[0]); pairs=[tuple(a[i:i+2]) for i in range(1,len(a),2)]
        return len(a)==1+2*k and len(set(pairs))==k and dict(pairs)==chains
    if tid=="taco_0137":
        n,k,piles=d
        if a[0].upper()=="NO":return len(a)==1 and max(piles)-min(piles)>k
        if a[0].upper()!="YES" or len(a)!=1+sum(piles):return False
        values=list(map(int,a[1:]));counts=[];offset=0
        for count in piles:
            row=values[offset:offset+count];offset+=count
            if any(not 1<=x<=k for x in row):return False
            counts.append(collections.Counter(row))
        return all(max(row[color] for row in counts)-min(row[color] for row in counts)<=1 for color in range(1,k+1))
    if tid=="lcb_atcoder_abc366_g":
        n,edges=d
        if a[0].lower()=="no":
            if len(a)!=1:return False
            # No solution iff a coordinate is zero throughout the adjacency nullspace:
            # its unit vector belongs to the row space. Prove this by elimination.
            basis={}
            for u in range(1,n+1):
                row=0
                for x,y in edges:
                    if x==u:row^=1<<(y-1)
                    if y==u:row^=1<<(x-1)
                while row:
                    b=row.bit_length()-1
                    if b in basis:row^=basis[b]
                    else:basis[b]=row;break
            for v in range(n):
                row=1<<v
                while row and row.bit_length()-1 in basis:row^=basis[row.bit_length()-1]
                if not row:return True
            return False
        if a[0].lower()!="yes" or len(a)!=n+1:return False
        values=list(map(int,a[1:]));z=[0]*n
        if any(not 1<=x<2**60 for x in values):return False
        for u,v in edges:z[u-1]^=values[v-1];z[v-1]^=values[u-1]
        return not any(z)
    x=list(map(int,a))
    if tid in {"taco_0594","taco_0056","taco_0422","taco_0771"}:
        offset=0
        for n in d:
            size=n*(n-1)//2 if tid=="taco_0422" else n
            row=x[offset:offset+size];offset+=size
            if len(row)!=size:return False
            if tid=="taco_0422":
                scores=[0]*n;draws=0;i=0
                for u in range(n):
                    for v in range(u+1,n):
                        value=row[i];i+=1
                        if value not in (-1,0,1):return False
                        if value==0:scores[u]+=1;scores[v]+=1;draws+=1
                        elif value==1:scores[u]+=3
                        else:scores[v]+=3
                if len(set(scores))!=1 or draws!=(0 if n%2 else n//2):return False
            else:
                begin=0 if tid=="taco_0056" else 1
                if sorted(row)!=list(range(begin,n+begin)):return False
                if tid=="taco_0594" and any(math.isqrt(a*b)**2==a*b for a,b in zip(row,row[1:])):return False
                if tid=="taco_0056" and any((a^b)&((a^b)-1) for a,b in zip(row,row[1:])):return False
                if tid=="taco_0771":
                    ordered=[];previous=None
                    for value in row:
                        bisect.insort(ordered,value);median=ordered[(len(ordered)-1)//2]
                        if median==previous:return False
                        previous=median
        return offset==len(x)
    if tid=="taco_0510":return len(x)==3 and min(x)>0 and d in sorted(x)[:2] and sorted(x)[0]**2+sorted(x)[1]**2==sorted(x)[2]**2
    if tid=="taco_0831":
        n=d;total=n*(n+1)//2
        return len(x)>=2 and x[0]==total%2 and x[1]==len(x)-2 and 0<x[1]<n and len(set(x[2:]))==x[1] and all(1<=v<=n for v in x[2:]) and abs(total-2*sum(x[2:]))==x[0]
    if tid=="taco_0946":
        l,r=d
        if x==[-1]:return (l if l%2==0 else l+1)+2>r
        return len(x)==3 and l<=x[0]<x[1]<x[2]<=r and math.gcd(x[0],x[1])==math.gcd(x[1],x[2])==1 and math.gcd(x[0],x[2])>1
    if tid=="taco_0054":
        correct=str(d[0]-d[1]);s=out.strip()
        return len(s)==len(correct) and s.isascii() and s.isdecimal() and s[0]!='0' and sum(a!=b for a,b in zip(s,correct))==1
    if tid=="taco_0552":
        n,k,prices=d;total=0;maximum=0
        for price in sorted(prices):
            if total+price>k:break
            total+=price;maximum+=1
        return x and x[0]==maximum and len(x)==maximum+1 and len(set(x[1:]))==maximum and all(1<=i<=n for i in x[1:]) and sum(prices[i-1] for i in x[1:])<=k
    if tid=="taco_0617":
        levels=d;maximum=min(levels.count(i) for i in (1,2,3));indices=x[1:]
        return x and x[0]==maximum and len(indices)==3*maximum and len(set(indices))==len(indices) and all(1<=i<=len(levels) for i in indices) and all(sorted(levels[j-1] for j in indices[i:i+3])==[1,2,3] for i in range(0,len(indices),3))
    if tid=="taco_0444":
        if len(x)!=2*len(d):return False
        for i,(u,v) in enumerate(d):
            a,b=x[2*i:2*i+2]
            if (a,b)==(0,0):
                if v%u==0:return False
            elif not (1<=a<=10**9 and 1<=b<=10**9):return False
            elif b==1:
                if u!=v:return False
            elif a>7 or u*pow(b,a)!=v:return False
        return True
    if tid=="taco_0519":
        if len(x)!=len(d):return False
        for point,(n,k,points) in zip(x,d):
            optimum=min((points[i+k]-points[i]+1)//2 for i in range(n-k))
            if sorted(abs(v-point) for v in points)[k]!=optimum:return False
        return True
    if tid=="taco_0638":
        # Grid rows are bit strings, not integer tokens.
        offset=0
        for n,k in d:
            score=int(a[offset]);grid=a[offset+1:offset+1+n];offset+=n+1
            if len(grid)!=n or any(len(r)!=n or set(r)-{'0','1'} for r in grid):return False
            rows=[r.count('1') for r in grid];cols=[sum(r[j]=='1' for r in grid) for j in range(n)]
            if sum(rows)!=k or score!=(max(rows)-min(rows))**2+(max(cols)-min(cols))**2 or score!=(0 if k%n==0 else 2):return False
        return offset==len(a)
    if tid=="taco_0574":
        n,m=d
        return len(x)==n*m and all(1<=v<=10**8 for v in x) and all(math.isqrt(s)**2==s for s in [sum(v*v for v in x[i*m:(i+1)*m]) for i in range(n)]+[sum(x[i*m+j]**2 for i in range(n)) for j in range(m)])
    if tid=="taco_0347":
        if len(x)!=2*len(d):return False
        n=len(d)
        for value,a,b in zip(d,x[:n],x[n:]):
            if a==b==-1:
                p=2
                while p*p<=value and value%p:p+=1
                if p*p>value:continue
                while value%p==0:value//=p
                if value!=1:return False
            elif not (a>1 and b>1 and value%a==value%b==0 and math.gcd(a+b,value)==1):return False
        return True
    if tid=="taco_0381":return len(x)==len(d) and all(0<=v<2**17 and sorted(y^v for y in a)==list(range(l,r+1)) for v,(l,r,a) in zip(x,d))
    if tid=="taco_0945":
        if len(x)!=len(d):return False
        for winner,athletes in zip(x,d):
            def beats(u,v):return sum(a<b for a,b in zip(athletes[u],athletes[v]))>=3
            if winner==-1:
                candidate=0
                for i in range(1,len(athletes)):
                    if beats(i,candidate):candidate=i
                if all(i==candidate or beats(candidate,i) for i in range(len(athletes))):return False
            elif not (1<=winner<=len(athletes)) or not all(i==winner-1 or beats(winner-1,i) for i in range(len(athletes))):return False
        return True
    if tid=="lcb_atcoder_abc350_c":
        n,p=d;p=p[:]
        if not x or not (0<=x[0]<=n and len(x)==1+2*x[0]):return False
        for i in range(x[0]):
            u,v=x[1+2*i]-1,x[2+2*i]-1
            if not (0<=u<n and 0<=v<n):return False
            p[u],p[v]=p[v],p[u]
        return p==list(range(1,n+1))
    if tid=="lcb_atcoder_abc311_c":
        n,nxt=d;k=x[0];cycle=x[1:]
        return 1<=k<=n and len(cycle)==k and len(set(cycle))==k and all(1<=v<=n and nxt[v-1]==cycle[(i+1)%k] for i,v in enumerate(cycle))
    if tid=="lcb_atcoder_abc315_e":
        needed=set();stack=[1]
        while stack:
            u=stack.pop()
            for v in d[u-1]:
                if v not in needed:needed.add(v);stack.append(v)
        pos={v:i for i,v in enumerate(x)}
        return len(x)==len(needed) and set(x)==needed and all(pos[v]<pos[u] for u in x for v in d[u-1])
    if tid=="lcb_atcoder_arc181_c":
        n,p,q=d;grid=a
        if len(grid)!=n or any(len(r)!=n or set(r)-{'0','1'} for r in grid):return False
        cols=[''.join(r[j] for r in grid) for j in range(n)]
        return all(grid[p[i]-1]<grid[p[i+1]-1] and cols[q[i]-1]<cols[q[i+1]-1] for i in range(n-1))
    raise KeyError(tid)

SUPPORTED.update(EXTRA_SUPPORTED)

SUPPORTED.update(MORE_SUPPORTED)
