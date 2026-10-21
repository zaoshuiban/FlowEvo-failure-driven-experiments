from typing import List

class Solution:
    def maxDistinctElements(self, nums: List[int], k: int) -> int:
        nums.sort()
        ans = 0
        last = -10**30

        for x in nums:
            chosen = max(x - k, last + 1)
            if chosen <= x + k:
                ans += 1
                last = chosen

        return ans