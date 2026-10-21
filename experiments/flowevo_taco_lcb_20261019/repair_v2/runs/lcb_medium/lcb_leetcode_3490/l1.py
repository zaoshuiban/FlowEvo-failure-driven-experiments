from typing import List

class Solution:
    def maximumLength(self, nums: List[int]) -> int:
        even_count = odd_count = 0
        end_even = end_odd = 0

        for num in nums:
            if num % 2 == 0:
                even_count += 1
                end_even = max(end_even, end_odd + 1)
            else:
                odd_count += 1
                end_odd = max(end_odd, end_even + 1)

        return max(even_count, odd_count, end_even, end_odd)