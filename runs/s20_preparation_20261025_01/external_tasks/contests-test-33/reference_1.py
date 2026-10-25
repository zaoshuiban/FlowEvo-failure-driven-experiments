import collections
import sys
import io, os
import math
from heapq import *

gcd = math.gcd
sqrt = math.sqrt


def ceil(a, b):
    a = -a
    k = a // b
    k = -k
    return k


# arr=list(map(int, input().split()))
input = io.BytesIO(os.read(0, os.fstat(0).st_size)).readline


def strinp(testcases):
    k = 5
    if (testcases == -1 or testcases == 1):
        k = 1
    f = str(input())
    f = f[2:len(f) - k]
    return f


def main():
    n=int(input())
    arr=list(map(int, input().split()))
    ma=max(arr)
    came=[-1]*(512)
    came[0]=0
    for i in range(n):
        no=arr[i]
        if(came[no]==-1):
            came[no]=no
        else:
            came[no]=min(no,came[no])
        for j in range(512):
            if(came[j]!=-1 and no>came[j]):
                b=j^no
                if(came[b]==-1):
                    came[b]=no
                else:
                    came[b]=min(came[b],no)
    ans=[]
    s=0
    for i in range(512):
        if(came[i]!=-1):
            s+=1
            ans.append(i)
    print(s)
    print(*ans)
                
                    
main()