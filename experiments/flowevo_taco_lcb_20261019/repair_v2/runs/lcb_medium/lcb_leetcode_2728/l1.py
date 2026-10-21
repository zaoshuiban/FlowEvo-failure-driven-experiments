from typing import List

class Solution:
    def matrixSum(self, nums: List[List[int]]) -> int:
        for row in nums:
            row.sort()
        
        score = 0
        cols = len(nums[0])
        
        for col in range(cols):
            score += max(row[col] for row in nums)
        
        return score