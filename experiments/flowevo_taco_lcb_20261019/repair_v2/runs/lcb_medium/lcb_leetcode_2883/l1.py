class Solution:
    def minimumBeautifulSubstrings(self, s: str) -> int:
        n = len(s)

        powers = set()
        value = 1
        while len(bin(value)) - 2 <= n:
            powers.add(bin(value)[2:])
            value *= 5

        INF = float("inf")
        dp = [INF] * (n + 1)
        dp[0] = 0

        for i in range(n):
            if dp[i] == INF:
                continue
            if s[i] == "0":
                continue

            for j in range(i + 1, n + 1):
                substring = s[i:j]
                if substring in powers:
                    dp[j] = min(dp[j], dp[i] + 1)

        return -1 if dp[n] == INF else dp[n]