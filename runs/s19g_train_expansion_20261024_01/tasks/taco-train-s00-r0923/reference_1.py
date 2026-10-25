for t in range(int(input())):
	n = int(input())
	a = list(map(int, input().split()))
	ans = sum(a[::2])
	total = 0
	maxn = 0
	for i in range(0, n - 1, 2):
		total += a[i + 1] - a[i]
		maxn = max(total, maxn)
		if total < 0:
			total = 0
	total2 = 0
	for i in range(1, n - 1, 2):
		total2 += a[i] - a[i + 1]
		maxn = max(total2, maxn)
		if total2 < 0:
			total2 = 0
	print(ans + maxn)
