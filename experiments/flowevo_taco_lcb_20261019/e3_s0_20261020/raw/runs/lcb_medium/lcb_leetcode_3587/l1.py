from typing import List

class Solution:
    def maxScore(self, n: int, k: int, stayScore: List[List[int]], travelScore: List[List[int]]) -> int:
        dp = [0] * n

        for day in range(k):
            next_dp = [0] * n

            for dest in range(n):
                best = dp[dest] + stayScore[day][dest]

                for curr in range(n):
                    best = max(best, dp[curr] + travelScore[curr][dest])

                next_dp[dest] = best

            dp = next_dp

        return max(dp)