from typing import List

class Solution:
    def maximumTripletValue(self, nums: List[int]) -> int:
        max_value = 0
        max_i = 0
        max_diff = 0

        for x in nums:
            max_value = max(max_value, max_diff * x)
            max_diff = max(max_diff, max_i - x)
            max_i = max(max_i, x)

        return max_value