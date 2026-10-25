from collections import Counter
for _ in range(int(input())):
	n = int(input())
	a = list(map(int, input().split()))
	x = Counter(a)
	m = max(x.values())
	s = list(x.values()).count(m)
	x = n - s * m
	x = x // (m - 1)
	print(x + s - 1)
