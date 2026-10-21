from typing import List

class Solution:
    def minOperations(self, nums: List[int], k: int) -> int:
        seen = set()
        operations = 0

        for i in range(len(nums) - 1, -1, -1):
            operations += 1
            if nums[i] <= k:
                seen.add(nums[i])

            if len(seen) == k:
                return operations

        return operations