from typing import List

class Solution:
    def constructTransformedArray(self, nums: List[int]) -> List[int]:
        n = len(nums)
        result = [0] * n

        for i, value in enumerate(nums):
            landing_index = (i + value) % n
            result[i] = nums[landing_index]

        return result