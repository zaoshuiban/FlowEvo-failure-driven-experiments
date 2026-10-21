from typing import List

class Solution:
    def alternatingSubarray(self, nums: List[int]) -> int:
        n = len(nums)
        ans = -1

        for i in range(n):
            for j in range(i + 1, n):
                expected = nums[i] + ((j - i) % 2)

                if nums[j] != expected:
                    break

                ans = max(ans, j - i + 1)

        return ans