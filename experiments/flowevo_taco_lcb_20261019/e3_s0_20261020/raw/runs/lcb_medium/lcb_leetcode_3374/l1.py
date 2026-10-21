from typing import List

class Solution:
    def countAlternatingSubarrays(self, nums: List[int]) -> int:
        total = 0
        current = 1

        for i in range(len(nums)):
            if i > 0 and nums[i] != nums[i - 1]:
                current += 1
            else:
                current = 1

            total += current

        return total