from sys import stdin, stdout
from math import floor, gcd, fabs, factorial, fmod, sqrt, inf, log
from collections import defaultdict as dd, deque
from heapq import merge, heapify, heappop, heappush, nsmallest
from bisect import bisect_left as bl, bisect_right as br, bisect
mod = pow(10, 9) + 7
mod2 = 998244353

def inp():
	return stdin.readline().strip()

def iinp():
	return int(inp())

def out(var, end='\n'):
	stdout.write(str(var) + '\n')

def outa(*var, end='\n'):
	stdout.write(' '.join(map(str, var)) + end)

def lmp():
	return list(mp())

def mp():
	return map(int, inp().split())

def smp():
	return map(str, inp().split())

def l1d(n, val=0):
	return [val for i in range(n)]

def l2d(n, m, val=0):
	return [l1d(m, val) for j in range(n)]

def remadd(x, y):
	return 1 if x % y else 0

def ceil(a, b):
	return (a + b - 1) // b
S1 = 'abcdefghijklmnopqrstuvwxyz'
S2 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def isprime(x):
	if x <= 1:
		return False
	if x in (2, 3):
		return True
	if x % 2 == 0:
		return False
	for i in range(3, int(sqrt(x)) + 1, 2):
		if x % i == 0:
			return False
	return True
for _ in range(int(inp())):
	(n, m) = mp()
	arr = lmp()
	mdn = l1d(70)
	if sum(arr) < n:
		print(-1)
		continue
	s = bin(n)[2:]
	for i in range(len(s)):
		if s[len(s) - 1 - i] == '1':
			mdn[i] = 1
	cnt = l1d(70)
	for i in arr:
		cnt[len(bin(i)) - 3] += 1
	ans = 0
	for i in range(70):
		if mdn[i]:
			if cnt[i]:
				cnt[i] -= 1
			else:
				sm = 2
				j = i - 1
				while j >= 0 and sm > 0:
					sm -= cnt[j]
					sm *= 2
					j -= 1
				if sm <= 0:
					sm = 2
					j = i - 1
					while j >= 0 and sm > 0:
						x = min(cnt[j], sm)
						sm -= x
						cnt[j] -= x
						sm *= 2
						j -= 1
				else:
					for j in range(i, 70):
						if cnt[j]:
							break
					for k in range(j, i, -1):
						cnt[k] -= 1
						cnt[k - 1] += 2
					if cnt[i]:
						cnt[i] -= 1
						ans += j - i
	print(ans)
