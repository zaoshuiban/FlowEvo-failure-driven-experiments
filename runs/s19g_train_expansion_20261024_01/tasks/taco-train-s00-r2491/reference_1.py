import sys
input = sys.stdin.readline
ans = []
for T in range(int(input())):
	(n, lst) = (int(input()), list(map(int, input().split())))
	(dp, i) = (n * [1], 1)
	while i <= n:
		j = 2 * i
		while j <= n:
			if lst[i - 1] < lst[j - 1]:
				dp[j - 1] = max(dp[j - 1], dp[i - 1] + 1)
			j += i
		i += 1
	ans.append(max(dp))
print(*ans, sep='\n')
