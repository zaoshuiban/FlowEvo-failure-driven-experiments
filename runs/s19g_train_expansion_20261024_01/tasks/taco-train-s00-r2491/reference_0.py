import math
t = int(input())

def divs(n):
	d = []
	for i in range(1, int(math.sqrt(n)) + 1):
		if n % i == 0:
			d.append(i)
			d.append(int(n / i))
	return d

def solve():
	n = int(input())
	ar = list(map(int, input().split()))
	maxes = []
	for i in range(len(ar)):
		d = divs(i + 1)
		m = 0
		for j in range(len(d)):
			if ar[d[j] - 1] < ar[i] and maxes[d[j] - 1] > m:
				m = maxes[d[j] - 1]
		maxes.append(m + 1)
	print(max(maxes))
for i in range(t):
	solve()
