import collections
import heapq
import sys
import math
import bisect
import os
from io import BytesIO, IOBase
input = sys.stdin.readline

def solve():
	(n, m) = list(map(int, input().split()))
	nn = n
	while n % 10 == 0:
		n //= 10
	tot = 1
	while n % 5 == 0 and tot * 2 <= m:
		tot *= 2
		n //= 5
	while n % 2 == 0 and tot * 5 <= m:
		tot *= 5
		n //= 2
	while tot * 10 <= m:
		tot *= 10
	print(nn * tot * (m // tot))
for i in range(int(input())):
	solve()
