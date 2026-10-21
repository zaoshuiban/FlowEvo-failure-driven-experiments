from typing import List

class Solution:
    def maxScore(self, nums: List[int], x: int) -> int:
        neg_inf = -10**30
        dp = [neg_inf, neg_inf]
        dp[nums[0] & 1] = nums[0]

        for value in nums[1:]:
            parity = value & 1
            best_previous = max(dp[parity], dp[parity ^ 1] - x)
            current_score = best_previous + value
            dp[parity] = max(dp[parity], current_score)

        return max(dp)