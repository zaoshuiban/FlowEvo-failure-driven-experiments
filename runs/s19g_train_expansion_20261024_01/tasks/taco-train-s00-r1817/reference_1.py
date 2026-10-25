def answer(n, d, A):
	A.sort(key=lambda x: x[0])
	pre = [0] * (n + 1)
	for i in range(1, n + 1):
		pre[i] = pre[i - 1] + A[i - 1][1]
	l = 0
	r = 0
	maxi = 0
	while r >= l and r < n:
		if A[r][0] - A[l][0] < d:
			r += 1
		else:
			maxi = max(maxi, pre[r] - pre[l])
			l += 1
	maxi = max(maxi, pre[r] - pre[l])
	return maxi
(n, d) = map(int, input().split())
arr = []
for i in range(n):
	(v, f) = map(int, input().split())
	arr.append([v, f])
print(answer(n, d, arr))
