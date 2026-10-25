(n, k) = map(int, input().split())
(s, p) = (input(), input())
(a, b) = (p[0], p[1])
if a == b:
	x = min(s.count(a) + k, n)
	print(x * (x - 1) >> 1)
else:
	dp = [[-10000] * (k + 2) for _ in range(n + 2)]
	dp[1][1] = 0
	for i in range(n):
		for q in range(i + 2, 0, -1):
			for t in range(min(k, i + 1) + 1, 0, -1):
				dp[q][t] = max(dp[q][t], dp[q - 1][t - (0 if s[i] == a else 1)], dp[q][t - (0 if s[i] == b else 1)] + q - 1)
	print(max((i for line in dp for i in line)))
