from typing import List

class Solution:
    def countArrays(self, original: List[int], bounds: List[List[int]]) -> int:
        base = original[0]
        low = -10**30
        high = 10**30

        for o, (u, v) in zip(original, bounds):
            shift = o - base
            low = max(low, u - shift)
            high = min(high, v - shift)

            if low > high:
                return 0

        return high - low + 1