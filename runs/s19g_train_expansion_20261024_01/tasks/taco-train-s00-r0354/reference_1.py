from os import path
from io import BytesIO, IOBase
import sys
from heapq import heappush, heappop
from functools import cmp_to_key as ctk
from collections import deque, Counter, defaultdict as dd
from bisect import bisect, bisect_left, bisect_right, insort, insort_left, insort_right
from itertools import permutations
from datetime import datetime
from math import ceil, sqrt, log, gcd

def ii():
	return int(input())

def si():
	return input().rstrip()

def mi():
	return map(int, input().split())

def li():
	return list(mi())
abc = 'abcdefghijklmnopqrstuvwxyz'
mod = 1000000007
inf = float('inf')
vow = ['a', 'e', 'i', 'o', 'u']
(dx, dy) = ([-1, 1, 0, 0], [0, 0, 1, -1])

def bo(i):
	return ord(i) - ord('0')
file = 1

def ceil(a, b):
	return (a + b - 1) // b

def solve():
	for _ in range(1, ii() + 1):
		s = si()
		n = len(s)
		x = [0] * 10
		for i in s:
			x[bo(i)] += 1

		def check(c9):
			cnt = 0
			c = 0
			for i in range(10):
				if x[i] & 1:
					cnt += 1
				c += x[i] % 2
				c %= 2
			c += c9 & 1
			c %= 2
			if c == 0 and cnt > c9:
				return 0
			if c == 1 and cnt > c9 + 1:
				return 0
			return 1
		ok = False
		last = -1
		for i in range(n - 1, -1, -1):
			x[bo(s[i])] -= 1
			for j in range(bo(s[i]) - 1, -1, -1):
				x[j] += 1
				if check(n - i - 1):
					ok = True
					if i == 0 and j == 0:
						n -= 1
						if n % 2 == 0:
							x = n
						else:
							x = n - 1
						res = '9' * x
					else:
						c = chr(48 + j)
						res = s[:i] + c + '9' * (n - i - 1)
					last = i
					break
				x[j] -= 1
			if ok:
				break
		n = len(res)
		x = [0] * 10
		for i in range(last + 1):
			x[bo(res[i])] += 1
		p = []
		for i in range(10):
			if x[i] & 1:
				p.append(i)
		if len(p) > 0:
			if n & 1:
				x = str(p[-1])
				p.pop()
			r = len(res) - 1
			res = list(res)
			for j in p:
				res[r] = str(j)
				r -= 1
			res = ''.join(res)
			for j in range(len(res)):
				if res[j] == x:
					print(res[:j] + res[j + 1:])
					break
		print(res)
if file:
	if path.exists('input.txt'):
		sys.stdin = open('input.txt', 'r')
		sys.stdout = open('output.txt', 'w')
	else:
		input = sys.stdin.readline
solve()
