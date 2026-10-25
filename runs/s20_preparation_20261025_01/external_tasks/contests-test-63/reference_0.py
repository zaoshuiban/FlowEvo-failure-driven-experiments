from sys import stdin, stdout
import sys
import heapq
from collections import defaultdict
import math
import bisect
import io, os
# from cffi import FFI
import copy
import itertools

# for interactive problem
# n = int(stdin.readline())
# print(x, flush=True)

#input = io.BytesIO(os.read(0, os.fstat(0).st_size)).readline

def ncr(n, r, p):
    # initialize numerator
    # and denominator
    num = den = 1
    for i in range(r):
        num = (num * (n - i)) % p
        den = (den * (i + 1)) % p
    return (num * pow(den,
            p - 2, p)) % p

#input = sys.stdin.buffer.readline

# ffi = FFI()
# ffi.cdef(
#     """
#     typedef struct {
#         long long suf;
#         long long pre;
#         long long maxi;
#         bool is_plus;
#         long long lowest;
#         long long sum;
#         int length;
#     } node_t;
#     """
# )
#
# MX = 2 << ((2 * 10 ** 5) - 1).bit_length()
# data = ffi.new("node_t[]", MX + 3)
# data[MX] = (0, 0, 0, True, 0, 0, 0)
# id_node = data[MX]
# res_left = MX + 1
# res_right = MX + 2
#
# def combine(a, b):
#     if a.length == 0:
#         return b
#     if b.length == 0:
#         return a
#
#     length = a.length + b.length
#     if a.is_plus:
#         pre = a.sum + b.pre
#     else:
#         pre = a.pre
#     if b.is_plus:
#         suf = a.suf + b.sum
#     else:
#         suf = b.suf
#     is_plus = a.is_plus and b.is_plus
#     sum = a.sum + b.sum
#     maxi = max(a.maxi, b.maxi, a.suf + b.pre)
#     lowest = min(a.lowest, a.sum + b.lowest)
#     return (suf, pre, maxi, is_plus, lowest, sum, length)
#
# def mapValue(x):
#     return (max(x, 0), max(x, 0), max(x, 0), (x >= 0), x, x, 1)
#
# class SegmentTree:
#     def __init__(self, N, A):
#         self._len = N
#         self._size = _size = 1 << (self._len - 1).bit_length()
#         for i in range(2 * _size):
#             data[i] = id_node
#         for i, x in enumerate(A):
#             data[_size + i] = mapValue(x)
#         for i in reversed(range(_size)):
#             data[i] = combine(data[i + i], data[i + i + 1])
#
#     def __delitem__(self, idx):
#         self[idx] = id_node
#
#     def __getitem__(self, idx):
#         return data[idx + self._size]
#
#     def __setitem__(self, idx, value):
#         idx += self._size
#         data[idx] = value
#         idx >>= 1
#         while idx:
#             data[idx] = combine(data[2 * idx], data[2 * idx + 1])
#             idx >>= 1
#
#     def __len__(self):
#         return self._len
#
#     def query(self, start, stop):
#         """func of data[start, stop)"""
#         start += self._size
#         stop += self._size
#         data[res_left] = id_node
#         data[res_right] = id_node
#         while start < stop:
#             if start & 1:
#                 data[res_left] = combine(data[res_left], data[start])
#                 start += 1
#             if stop & 1:
#                 stop -= 1
#                 data[res_right] = combine(data[stop], data[res_right])
#             start >>= 1
#             stop >>= 1
#         data[res_left] = combine(data[res_left], data[res_right])
#         return data[res_left]

# def main():
#     n, q = map(int, stdin.readline().split())
#     segtree = SegmentTree(n, map(int, stdin.readline().split()))
#     ans = []
#     for _ in range(q):
#         t, l, r = map(int, stdin.readline().split())
#         l -= 1
#         if t == 1:
#             segtree[l] = mapValue(r)
#         else:
#             ans.append(int(segtree.query(l, r).ans))
#     print("\n".join(map(str, ans)))

def kbits(n, k):
    result = []
    for bits in itertools.combinations(range(n), k):
        s = ['0'] * n
        for bit in bits:
            s[bit] = '1'
        result.append(''.join(s))
    return result


def main():
    n = int(stdin.readline())
    cnt = [[] for _ in range(n)]
    L = []
    R = []
    for i in range(n):
        l, r = 0, 0
        st = stdin.readline().strip()
        for _ in range(len(st)+1):
            cnt[i].append(0)
        for x in st:
            if x == ')':
                if r > 0:
                    r -= 1
                    if r == 0:
                        cnt[i][l] += 1
                else:
                    l += 1
            else:
                 r += 1
        L.append(l)
        R.append(r)
    dp = [-1] * pow(2,n)
    dp[0] = 0
    dp_mx = [0] * pow(2,n)
    ans = 0
    for c in range(n):
        if c == 0:
            perm = ['0' * n]
        else:
            perm = kbits(n, c)
        for p in perm:
            num = int(p, 2)
            if dp[num] == -1:
                continue
            k = 1
            for i, s in enumerate(reversed(p)):
                if s == '0':
                    bal = dp[num]
                    sm = dp_mx[num]
                    if bal - L[i] > 0:
                        bal -= (L[i] - R[i])
                        dp[num + k] = bal
                        dp_mx[num + k] = max(sm, dp_mx[num + k])
                        ans = max(dp_mx[num + k], ans)
                    elif bal - L[i] == 0:
                        if bal > 0:
                            sm += 1
                        sm += cnt[i][L[i]]
                        dp[num + k] = R[i]
                        dp_mx[num + k] = max(sm, dp_mx[num + k])
                        ans = max(dp_mx[num + k], ans)
                    else:
                        sm += cnt[i][bal]
                        if bal > 0:
                            sm += 1
                        ans = max(sm, ans)

                k *= 2

    if ans == 3 and n == 5:
        print(L)
        print(R)
        print(dp_mx)
    stdout.write(str(ans)+"\n")


main()