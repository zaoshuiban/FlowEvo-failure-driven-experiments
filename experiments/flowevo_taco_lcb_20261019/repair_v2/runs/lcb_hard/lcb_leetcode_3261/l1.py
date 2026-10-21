from typing import List

class Solution:
    def minOrAfterOperations(self, nums: List[int], k: int) -> int:
        n = len(nums)
        need = n - k
        ALL = (1 << 30) - 1

        def feasible(allowed: int) -> bool:
            bad = ALL ^ allowed
            segments = 0
            cur = ALL

            for x in nums:
                cur &= x
                if (cur & bad) == 0:
                    segments += 1
                    if segments >= need:
                        return True
                    cur = ALL

            return False

        ans = 0

        for bit in range(29, -1, -1):
            candidate = ans | ((1 << bit) - 1)
            if not feasible(candidate):
                ans |= 1 << bit

        return ans