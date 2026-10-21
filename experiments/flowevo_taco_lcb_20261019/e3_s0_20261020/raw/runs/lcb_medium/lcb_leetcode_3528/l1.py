from typing import List

class Solution:
    def findMaximumScore(self, nums: List[int]) -> int:
        max_val = 0
        score = 0

        for i in range(len(nums) - 1):
            max_val = max(max_val, nums[i])
            score += max_val

        return score