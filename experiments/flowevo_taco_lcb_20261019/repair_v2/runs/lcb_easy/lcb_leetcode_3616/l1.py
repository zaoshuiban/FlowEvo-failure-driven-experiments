from typing import List

class Solution:
    def countValidSelections(self, nums: List[int]) -> int:
        total = sum(nums)
        left = 0
        ans = 0

        for x in nums:
            if x == 0:
                right = total - left
                diff = abs(left - right)

                if diff == 0:
                    ans += 2
                elif diff == 1:
                    ans += 1

            left += x

        return ans