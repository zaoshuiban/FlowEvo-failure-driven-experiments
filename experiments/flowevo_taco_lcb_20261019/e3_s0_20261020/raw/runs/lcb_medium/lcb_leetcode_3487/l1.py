from typing import List

class Solution:
    def maxRemovals(self, source: str, pattern: str, targetIndices: List[int]) -> int:
        n, m = len(source), len(pattern)

        is_target = [False] * n
        for idx in targetIndices:
            is_target[idx] = True

        INF = 10**9
        # dp[j] = minimum number of target positions used to match
        # the first j characters of pattern.
        dp = [INF] * (m + 1)
        dp[0] = 0

        for i, ch in enumerate(source):
            cost = 1 if is_target[i] else 0

            for j in range(m, 0, -1):
                if ch == pattern[j - 1] and dp[j - 1] != INF:
                    dp[j] = min(dp[j], dp[j - 1] + cost)

        return len(targetIndices) - dp[m]