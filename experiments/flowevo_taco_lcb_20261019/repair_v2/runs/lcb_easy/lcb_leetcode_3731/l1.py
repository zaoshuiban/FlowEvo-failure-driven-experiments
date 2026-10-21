from typing import List

class Solution:
    def subarraySum(self, nums: List[int]) -> int:
        n = len(nums)
        prefix = [0] * (n + 1)
        
        for i in range(n):
            prefix[i + 1] = prefix[i] + nums[i]
        
        total = 0
        for i in range(n):
            start = max(0, i - nums[i])
            total += prefix[i + 1] - prefix[start]
        
        return total