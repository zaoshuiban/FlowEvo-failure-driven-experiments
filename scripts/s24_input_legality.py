"""Task-specific statement grammar checks, not solver or correctness oracles."""
import re

def integers(s):
    tokens=s.split()
    if not all(re.fullmatch(r'-?\d+',t) for t in tokens):raise ValueError('NON_INTEGER_TOKEN')
    return list(map(int,tokens))
def validate(tid,s):
    def require(ok,why):
        if not ok:raise ValueError(why)
    try:
        if tid.endswith('r0704'):
            rows=s.strip().splitlines();require(bool(rows),'EMPTY');n=int(rows[0].strip());seq=[t.strip() for t in rows[1:]]
            require(1<=n<=100000,'N_RANGE');require(len(seq)==n,'SEQUENCE_COUNT');require(all(re.fullmatch(r'[()]+',z) for z in seq),'BRACKET_ALPHABET');require(sum(map(len,seq))<=500000,'TOTAL_LENGTH')
        else:
            a=integers(s);require(bool(a),'EMPTY')
            if tid.endswith('test-549'):
                require(len(a)==5,'FIELD_COUNT');n,m,k,x,y=a
                require(1<=n<=100 and 1<=m<=100,'GRID_RANGE');require(1<=k<=10**18,'K_RANGE');require(1<=x<=n and 1<=y<=m,'POSITION_RANGE')
            elif tid.endswith('r0493'):
                require(len(a)>=4,'FIELD_COUNT');n,m=a[:2];require(1<=n<=10**6 and 2<=m<=min(n+1,10000),'N_M_RANGE');require(len(a)==m+4,'ISLAND_COUNT');d=a[2:2+m];g,r=a[-2:]
                require(len(set(d))==m,'DISTINCT_ISLANDS');require(all(0<=z<=n for z in d),'ISLAND_OUTSIDE_ROAD');require(0 in d and n in d,'MISSING_ENDPOINT');require(1<=g<=1000 and 1<=r<=1000,'LIGHT_RANGE')
            elif tid.endswith('r2804'):
                q=a[0];require(1<=q<=500,'QUERY_COUNT_RANGE');require(len(a)==q+1,'QUERY_COUNT');require(all(1<=k<=10**9 for k in a[1:]),'K_RANGE')
            elif tid.endswith('test-91'):
                n=a[0];require(2<=n<=100000,'N_RANGE');require(len(a)==n,'PARENT_COUNT');require(all(1<=v<i for i,v in enumerate(a[1:],2)),'PARENT_ORDER_RANGE')
            elif tid.endswith('r0712'):
                n=a[0];require(1<=n<=100000,'N_RANGE');require(len(a)==1+2*n,'ARRAY_LENGTH');require(all(0<=v<=10**9 for v in a[1:]),'V_T_RANGE')
            else:raise ValueError('UNSUPPORTED_TASK')
        return dict(valid=True)
    except (ValueError,IndexError) as ex:return dict(valid=False,reason=str(ex))
