s = 0
n = int(input())
dp = [0] * (10 ** 5 + 1)
sec = [int(x) for x in input().split()]
ls = [0] * (10 ** 5 + 1)
for x in sec:
	ls[x] += 1
dp[1] = ls[1]
for i in range(2, 10 ** 5 + 1):
	dp[i] = max(dp[i - 1], dp[i - 2] + ls[i] * i)
print(dp[10 ** 5])
