from typing import List

class Solution:
    def distinctDifferenceArray(self, nums: List[int]) -> List[int]:
        n = len(nums)
        
        prefix = [0] * n
        seen = set()
        for i in range(n):
            seen.add(nums[i])
            prefix[i] = len(seen)
        
        suffix = [0] * (n + 1)
        seen.clear()
        for i in range(n - 1, -1, -1):
            seen.add(nums[i])
            suffix[i] = len(seen)
        
        return [prefix[i] - suffix[i + 1] for i in range(n)]