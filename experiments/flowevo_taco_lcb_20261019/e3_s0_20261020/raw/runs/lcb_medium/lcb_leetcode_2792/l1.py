from typing import List

class Solution:
    def doesValidArrayExist(self, derived: List[int]) -> bool:
        xor_sum = 0
        for x in derived:
            xor_sum ^= x
        return xor_sum == 0