import sys
from math import *
from collections import Counter as cc, defaultdict as df

def counter(l):
	return dict(cc(l))

def lcm(a, b):
	return int(a * b / gcd(a, b))

def input():
	return sys.stdin.readline().strip()

def ini():
	return int(input())

def inp():
	return map(int, input().split())

def li():
	return list(map(int, input().split()))
n = ini()
l = li()
s = input()
m = -1
c = 1
for i in range(n - 1):
	m = max(m, l[i])
	if s[i] == '0':
		if i + 1 < m:
			print('NO')
			c = 0
			break
if c:
	print('YES')
