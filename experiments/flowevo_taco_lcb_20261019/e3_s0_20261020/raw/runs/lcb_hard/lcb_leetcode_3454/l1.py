from typing import List

class Solution:
    def minimumOperations(self, nums: List[int], target: List[int]) -> int:
        ans = 0
        prev = 0

        for num, tar in zip(nums, target):
            cur = tar - num
            if cur > prev:
                ans += cur - prev
            prev = cur

        if prev < 0:
            ans += -prev

        return ans