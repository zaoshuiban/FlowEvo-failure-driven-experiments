import sys
import math
import random
import heapq
#sys.setrecursionlimit(10**6)
input=sys.stdin.readline
def pow(a,n):
    if n==0:
        return 1 
    x=pow(a,n//2)
    if n%2==0 :
        return (x*x)
    else:
        return (x*x*a)
 
def gcd(a,b):
    while b!=0:
        a,b=b,a%b
    return a 
    
def bs(arr,le,ri):
    l=0
    arr.sort()
    r=len(arr)-1
    ans=10000000
    while l<=r:
        m=(l+r)//2
        if arr[m]>=le and arr[m]<=ri:
            ans=arr[m]
            r=m-1
        elif arr[m]<le:
            l=m+1 
        else:
            r=m-1
    return ans
 
# t=int(input())
t=1
while t>0:
    n=int(input())
    a=list(map(int,input().split()))
    d={} 
    l=[512]*512
    l[0]=0
    for i in a:
        for j in range(512):
            if l[j]<i:
                l[i^j]=min(l[i^j],i)
    ls=[]
    c=0
    for i in range(512):
        if l[i]<512:
            c+=1
            ls.append(i)
    print(c)
    print(" ".join(map(str,ls)))
    t-=1