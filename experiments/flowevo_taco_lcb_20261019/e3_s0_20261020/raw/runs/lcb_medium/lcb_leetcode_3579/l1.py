from typing import List
from itertools import permutations

class Solution:
    def maxGoodNumber(self, nums: List[int]) -> int:
        binary = [bin(x)[2:] for x in nums]
        ans = 0

        for p in permutations(binary):
            ans = max(ans, int("".join(p), 2))

        return ans