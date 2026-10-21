from typing import List

class Solution:
    def minChanges(self, nums: List[int], k: int) -> int:
        n = len(nums)
        m = n // 2

        diff_freq = [0] * (k + 1)
        t_freq = [0] * (k + 1)

        for i in range(m):
            a = nums[i]
            b = nums[n - 1 - i]

            if a > b:
                a, b = b, a

            diff_freq[b - a] += 1

            t = max(b, k - a)
            t_freq[t] += 1

        suffix = [0] * (k + 2)
        running = 0

        for x in range(k, -1, -1):
            running += t_freq[x]
            suffix[x] = running

        ans = 2 * m

        for x in range(k + 1):
            cost = 2 * m - suffix[x] - diff_freq[x]
            if cost < ans:
                ans = cost

        return ans