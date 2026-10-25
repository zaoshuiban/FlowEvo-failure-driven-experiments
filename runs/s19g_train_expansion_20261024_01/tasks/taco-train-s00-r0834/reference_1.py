for _ in range(int(input())):
	n = int(input())
	cnt = [0 for i in range(n + 1)]
	b = list(map(int, input().split()))
	for u in b:
		cnt[u] += 1
	mxfq = max(cnt)
	tot = 0
	for u in cnt:
		tot += min(u, mxfq - 1)
	print((tot - (mxfq - 1)) // (mxfq - 1))
