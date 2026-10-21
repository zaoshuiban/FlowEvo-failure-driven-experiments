from typing import List

class Solution:
    def canAliceWin(self, nums: List[int]) -> bool:
        single_sum = 0
        double_sum = 0
        total_sum = 0

        for num in nums:
            total_sum += num
            if num < 10:
                single_sum += num
            else:
                double_sum += num

        return 2 * single_sum > total_sum or 2 * double_sum > total_sum