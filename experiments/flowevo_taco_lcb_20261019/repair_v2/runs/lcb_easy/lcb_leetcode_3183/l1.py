from typing import List

class Solution:
    def findKOr(self, nums: List[int], k: int) -> int:
        result = 0

        for bit in range(31):
            count = sum((num >> bit) & 1 for num in nums)
            if count >= k:
                result |= 1 << bit

        return result