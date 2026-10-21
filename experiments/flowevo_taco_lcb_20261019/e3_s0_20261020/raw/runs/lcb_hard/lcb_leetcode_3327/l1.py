from typing import List

class Solution:
    def minimumMoves(self, nums: List[int], k: int, maxChanges: int) -> int:
        positions = [i for i, x in enumerate(nums) if x == 1]
        m = len(positions)

        prefix = [0] * (m + 1)
        for i, p in enumerate(positions):
            prefix[i + 1] = prefix[i] + p

        def min_original_cost(t: int) -> int:
            if t == 0:
                return 0

            best = 10**18

            for left in range(m - t + 1):
                right = left + t
                mid = left + (t - 1) // 2
                median = positions[mid]

                left_cost = (
                    median * (mid - left)
                    - (prefix[mid] - prefix[left])
                )
                right_cost = (
                    (prefix[right] - prefix[mid + 1])
                    - median * (right - mid - 1)
                )

                best = min(best, left_cost + right_cost)

            return best

        required_originals = max(0, k - maxChanges)
        answer = 10**18

        upper = min(k, m, required_originals + 5)

        for take in range(required_originals, upper + 1):
            changes = k - take
            if 0 <= changes <= maxChanges and take <= m and take <= k:
                cost = min_original_cost(take) + 2 * changes
                answer = min(answer, cost)

        return answer