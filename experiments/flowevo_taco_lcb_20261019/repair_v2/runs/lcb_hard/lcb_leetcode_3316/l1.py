from typing import List

class Solution:
    def sumOfPowers(self, nums: List[int], k: int) -> int:
        MOD = 10**9 + 7
        nums.sort()
        n = len(nums)

        diffs = set()
        for i in range(n):
            for j in range(i + 1, n):
                d = nums[j] - nums[i]
                if d > 0:
                    diffs.add(d)

        if not diffs:
            return 0

        sorted_diffs = sorted(diffs)

        def count_ways(min_gap: int) -> int:
            # dp[i] = number of valid subsequences of current length ending at i
            dp = [1] * n

            if k == 1:
                return n % MOD

            for _ in range(2, k + 1):
                prefix = [0] * (n + 1)
                total = 0
                for i in range(n):
                    total += dp[i]
                    if total >= MOD:
                        total -= MOD
                    prefix[i + 1] = total

                cur = [0] * n
                r = 0

                for i in range(n):
                    limit = nums[i] - min_gap
                    while r < n and nums[r] <= limit:
                        r += 1
                    cur[i] = prefix[r]

                dp = cur

            result = 0
            for value in dp:
                result += value
                if result >= MOD:
                    result -= MOD
            return result

        answer = 0
        previous = 0

        for current in sorted_diffs:
            length = current - previous
            ways = count_ways(previous + 1)
            answer = (answer + (length % MOD) * ways) % MOD
            previous = current

        return answer