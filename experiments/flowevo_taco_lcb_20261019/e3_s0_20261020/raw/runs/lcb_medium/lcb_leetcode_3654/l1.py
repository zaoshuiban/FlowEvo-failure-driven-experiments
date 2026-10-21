from typing import List

class Solution:
    def minArraySum(self, nums: List[int], k: int, op1: int, op2: int) -> int:
        INF = 10**18
        dp = [[INF] * (op2 + 1) for _ in range(op1 + 1)]
        dp[0][0] = 0

        for x in nums:
            ndp = [[INF] * (op2 + 1) for _ in range(op1 + 1)]
            half = (x + 1) // 2
            can_subtract = x >= k

            for used1 in range(op1 + 1):
                for used2 in range(op2 + 1):
                    cur = dp[used1][used2]
                    if cur == INF:
                        continue

                    # Apply no operation
                    ndp[used1][used2] = min(ndp[used1][used2], cur + x)

                    # Apply operation 1 only
                    if used1 < op1:
                        ndp[used1 + 1][used2] = min(
                            ndp[used1 + 1][used2], cur + half
                        )

                    # Apply operation 2 only
                    if used2 < op2 and can_subtract:
                        ndp[used1][used2 + 1] = min(
                            ndp[used1][used2 + 1], cur + x - k
                        )

                    # Apply both operations to this index
                    if used1 < op1 and used2 < op2:
                        best = INF

                        # Operation 1 first, then operation 2
                        if half >= k:
                            best = min(best, half - k)

                        # Operation 2 first, then operation 1
                        if can_subtract:
                            after_sub = x - k
                            best = min(best, (after_sub + 1) // 2)

                        if best != INF:
                            ndp[used1 + 1][used2 + 1] = min(
                                ndp[used1 + 1][used2 + 1], cur + best
                            )

            dp = ndp

        return min(min(row) for row in dp)