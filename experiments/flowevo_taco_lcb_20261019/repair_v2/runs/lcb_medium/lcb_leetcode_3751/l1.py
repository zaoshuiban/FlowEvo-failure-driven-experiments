from typing import List

class Solution:
    def maxFrequency(self, nums: List[int], k: int) -> int:
        total_k = sum(1 for x in nums if x == k)
        ans = total_k

        for v in set(nums):
            if v == k:
                continue

            cur = 0
            best = 0

            for x in nums:
                if x == v:
                    cur += 1
                elif x == k:
                    cur -= 1

                if cur < 0:
                    cur = 0
                elif cur > best:
                    best = cur

            ans = max(ans, total_k + best)

        return ans