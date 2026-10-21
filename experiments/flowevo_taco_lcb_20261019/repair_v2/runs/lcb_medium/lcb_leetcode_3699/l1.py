from typing import List
from math import gcd
from collections import defaultdict

class Solution:
    def numberOfSubsequences(self, nums: List[int]) -> int:
        n = len(nums)
        ratio_count = defaultdict(int)
        answer = 0

        for r in range(n):
            # Add all valid pairs (p, q) with q = r - 2
            q = r - 2
            if q >= 2:
                den = nums[q]
                for p in range(q - 1):  # p <= q - 2
                    num = nums[p]
                    g = gcd(num, den)
                    ratio_count[(num // g, den // g)] += 1

            # Count valid s for the current r
            den_r = nums[r]
            for s in range(r + 2, n):
                num_s = nums[s]
                g = gcd(num_s, den_r)
                answer += ratio_count[(num_s // g, den_r // g)]

        return answer