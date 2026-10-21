from typing import List

class Solution:
    def minZeroArray(self, nums: List[int], queries: List[List[int]]) -> int:
        n = len(nums)
        m = len(queries)

        def can(k: int) -> bool:
            for i in range(n):
                target = nums[i]
                if target == 0:
                    continue

                dp = 1
                mask = (1 << (target + 1)) - 1

                for j in range(k):
                    l, r, val = queries[j]
                    if l <= i <= r:
                        dp |= dp << val
                        dp &= mask
                        if dp & (1 << target):
                            break

                if not (dp & (1 << target)):
                    return False

            return True

        if not can(m):
            return -1

        lo, hi = 0, m
        while lo < hi:
            mid = (lo + hi) // 2
            if can(mid):
                hi = mid
            else:
                lo = mid + 1

        return lo