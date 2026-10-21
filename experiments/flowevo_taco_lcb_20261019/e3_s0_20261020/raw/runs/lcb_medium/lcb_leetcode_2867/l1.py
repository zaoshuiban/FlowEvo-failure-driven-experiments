from typing import List

class Solution:
    def numberOfGoodSubarraySplits(self, nums: List[int]) -> int:
        MOD = 10**9 + 7
        ans = 1
        prev_one = -1

        for i, num in enumerate(nums):
            if num == 1:
                if prev_one == -1:
                    prev_one = i
                else:
                    ans = (ans * (i - prev_one)) % MOD
                    prev_one = i

        return ans if prev_one != -1 else 0