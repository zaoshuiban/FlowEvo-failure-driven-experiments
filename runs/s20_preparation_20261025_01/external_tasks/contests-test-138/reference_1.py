import io, os
import sys 
from sys import stdin

from bisect import bisect_left, bisect_right
from collections import defaultdict, deque, namedtuple
from heapq import heappush, heappop
from math import gcd, ceil, floor, factorial, sqrt
from itertools import accumulate, combinations, permutations

input = sys.stdin.buffer.readline
# input = io.BytesIO(os.read(0,os.fstat(0).st_size)).readline
# input = sys.stdin.readline

def find(p, x):
    if x != p[x]:
        p[x] = find(p, p[x])
    return p[x]

def union(a, b, p, cnt, sums, maxv):
    f1, f2 = find(p, a), find(p, b)
    if f1 != f2:
        if f1 < f2:
            f1, f2 = f2, f1 
        p[f2] = f1 
        l1, l2 = cnt[f1], cnt[f2]
        l3 = l1 + l2 
        cnt[f1] = l3 
        maxv += sums[f1 + 1 - l1] - sums[f1 + 1 - l3] - (sums[f2 + 1] - sums[f2 + 1 - l2])
    
    return maxv 

def work(a, b, qs):
    n, m = len(a), len(b)
    nums = a + b 
    nums.sort()
    sums = [0] + list(accumulate(nums))

    tot = n + m 
    f = list(range(tot))
    cnt = [0] * tot 
    maxv = sum(a)

    # DSU

    i = j = 0 
    while i < n:
        while a[i] != nums[j]:
            j += 1 
        cnt[j] = 1 
        i += 1 
        j += 1 
    
    mg = []
    ans = [0] * len(qs)
    for i in range(tot - 1):
        mg.append((nums[i + 1] - nums[i], i, i + 1))
    mg.sort(key=lambda x: x[0], reverse=True)

    for k, idx in qs:
        while mg and mg[-1][0] <= k:
            _, i, j = mg.pop()
            maxv = union(i, j, f, cnt, sums, maxv)
        ans[idx] = maxv 
    
    print("\n".join(map(str, ans)))    
    return 

# sys.setrecursionlimit(200010)
def main():
    test = 1

    for idt in range(test):
        # n = int(input())
        n, m, q = map(int, input().split())
        a = list(map(int, input().split()))
        b = list(map(int, input().split()))
        # q = list(map(int, input().split()))
        qs = sorted(zip(list(map(int, input().split())), range(q)))   # 元组 (数值， 原数组中的下标)
        a.sort()
        b.sort()

        work(a, b, qs)

    return 


if __name__ == '__main__':
    main()