for _ in range(int(input())):
	n = int(input())
	a = list(map(int, input().split()))
	m = 0
	best = max(abs(a[-1] - a[-2]), abs(a[1] - a[0]))
	for i in range(n - 2, -1, -1):
		m += abs(a[i + 1] - a[i])
		if i + 2 < n:
			best = max(best, -abs(a[i] - a[i + 2]) + (abs(a[i] - a[i + 1]) + abs(a[i + 1] - a[i + 2])))
	print(m - best)
