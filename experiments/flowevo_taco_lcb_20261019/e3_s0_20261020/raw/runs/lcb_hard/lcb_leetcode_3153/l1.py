from typing import List

class Solution:
    def maxSum(self, nums: List[int], k: int) -> int:
        MOD = 10**9 + 7
        counts = [0] * 31  # Enough for nums[i] <= 10^9

        for x in nums:
            b = 0
            while x:
                if x & 1:
                    counts[b] += 1
                x >>= 1
                b += 1

        ans = 0

        for i in range(k):
            value = 0
            for b, c in enumerate(counts):
                if c > i:
                    value |= 1 << b
            ans = (ans + value * value) % MOD

        return ans