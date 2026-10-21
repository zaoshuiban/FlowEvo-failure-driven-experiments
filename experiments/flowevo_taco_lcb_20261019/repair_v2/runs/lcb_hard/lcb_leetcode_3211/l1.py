from typing import List
from collections import deque

class Solution:
    def findMaximumLength(self, nums: List[int]) -> int:
        n = len(nums)
        prefix = [0] * (n + 1)

        for i, x in enumerate(nums, 1):
            prefix[i] = prefix[i - 1] + x

        dp = [0] * (n + 1)
        last = [0] * (n + 1)

        q = deque([0])

        for i in range(1, n + 1):
            while len(q) >= 2 and prefix[q[1]] + last[q[1]] <= prefix[i]:
                q.popleft()

            j = q[0]
            dp[i] = dp[j] + 1
            last[i] = prefix[i] - prefix[j]

            current = prefix[i] + last[i]
            while q and prefix[q[-1]] + last[q[-1]] >= current:
                q.pop()

            q.append(i)

        return dp[n]