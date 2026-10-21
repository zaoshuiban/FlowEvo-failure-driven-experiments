from typing import List

class Solution:
    def maxScore(self, a: List[int], b: List[int]) -> int:
        NEG_INF = -10**30
        dp = [NEG_INF] * 4

        for x in b:
            for j in range(3, -1, -1):
                if j == 0:
                    dp[0] = max(dp[0], a[0] * x)
                elif dp[j - 1] != NEG_INF:
                    dp[j] = max(dp[j], dp[j - 1] + a[j] * x)

        return dp[3]