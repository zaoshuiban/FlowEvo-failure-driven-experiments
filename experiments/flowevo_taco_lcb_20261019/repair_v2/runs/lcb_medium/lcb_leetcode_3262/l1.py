from typing import List

class Solution:
    def largestPerimeter(self, nums: List[int]) -> int:
        nums.sort()
        prefix = nums[0]
        answer = -1

        for i in range(1, len(nums)):
            if prefix > nums[i]:
                answer = max(answer, prefix + nums[i])
            prefix += nums[i]

        return answer