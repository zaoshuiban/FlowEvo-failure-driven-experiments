from typing import List

class Solution:
    def countCompleteDayPairs(self, hours: List[int]) -> int:
        count = 0
        remainder_count = [0] * 24

        for hour in hours:
            remainder = hour % 24
            needed = (24 - remainder) % 24
            count += remainder_count[needed]
            remainder_count[remainder] += 1

        return count