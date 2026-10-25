import sys
import math
input = sys.stdin.readline
h = {}

def ncr(n, r, p):
	num = den = 1
	for i in range(r):
		num = num * (n - i) % p
		den = den * (i + 1) % p
	return num * pow(den, p - 2, p) % p
T = int(input())
for _ in range(T):
	n = int(input())
	s = input().rstrip()
	prev = 'x'
	cnt_zero = 0
	cnt_group = 0
	for t in s:
		if t == '0':
			cnt_zero += 1
			prev = t
		elif prev == '1':
			cnt_group += 1
			prev = 'x'
		else:
			prev = t
	answer = ncr(cnt_zero + cnt_group, cnt_zero, 998244353)
	print(answer)
