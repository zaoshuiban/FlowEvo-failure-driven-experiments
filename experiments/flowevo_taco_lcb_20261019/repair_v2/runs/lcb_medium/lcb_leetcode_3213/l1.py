from typing import List

class Solution:
    def countSubarrays(self, nums: List[int], k: int) -> int:
        maximum = max(nums)
        ans = 0
        left = 0
        count_max = 0

        for right, value in enumerate(nums):
            if value == maximum:
                count_max += 1

            while count_max >= k:
                if nums[left] == maximum:
                    count_max -= 1
                left += 1

            ans += left

        return ans