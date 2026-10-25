import sys
from math import factorial, gcd
#from math import comb, perm    
from collections import Counter, deque, defaultdict
from bisect import bisect_left, bisect_right 
from heapq import heappop, heappush, heapify, nlargest, nsmallest
from itertools import groupby
from copy import deepcopy
MOD = 10**9+7
INF = float('inf')

# import io,os
# input = io.BytesIO(os.read(0,os.fstat(0).st_size)).readline
# input = sys.stdin.buffer.readline
input = sys.stdin.readline
rl = lambda : list(map(int, input().split()))
rs = lambda : sys.stdin.readline().strip()

def update(index, val):
    while index < len(BIT):
        BIT[index] += val
        index += index&-index

def sumQuery(index):
    total = 0
    while index > 0:
        total += BIT[index]
        index -= index&-index

    return total

def rangeQuery(l,r):
    return sumQuery(r) - sumQuery(l-1)


for _ in range(int(input())):
    n = int(input())
    A = rl()
    compressionD = {a: i + 1 for i, a in enumerate(sorted(set(A)))}
    A = [compressionD[a] for a in A]
    BIT = [0] * (len(compressionD)+1)
    count = 0
    for a in A:
        x = rangeQuery(1, a - 1)
        y = rangeQuery(a+1, len(compressionD))
        count += min(x, y)
        update(a, 1)

    print(count)