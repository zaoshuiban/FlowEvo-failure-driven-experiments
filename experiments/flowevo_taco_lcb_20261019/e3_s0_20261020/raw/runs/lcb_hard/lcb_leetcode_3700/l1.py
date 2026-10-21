from typing import List
from collections import Counter, defaultdict

class Solution:
    def subsequencesWithMiddleMode(self, nums: List[int]) -> int:
        MOD = 1_000_000_007
        n = len(nums)

        total = Counter(nums)
        right = Counter(nums)
        left = defaultdict(int)

        values = list(total.keys())

        def c2(x: int) -> int:
            return x * (x - 1) // 2 if x >= 2 else 0

        left_same = 0
        right_same = sum(c * (c - 1) // 2 for c in right.values())

        ans = 0

        for m, x in enumerate(nums):
            old_rx = right[x]
            right_same -= old_rx - 1
            right[x] = old_rx - 1

            lx = left.get(x, 0)
            rx = right[x]

            left_size = m
            right_size = n - m - 1

            non_left = left_size - lx
            non_right = right_size - rx

            total_pairs = c2(left_size) * c2(right_size)

            left0 = c2(non_left)
            right0 = c2(non_right)
            left1 = lx * non_left
            right1 = rx * non_right

            ways0 = left0 * right0
            ways1 = left1 * right0 + left0 * right1

            # Cases where x already appears at least 3 times among the 5 chosen elements.
            good_ge3 = total_pairs - ways0 - ways1

            sum_a = 0
            sum_b = 0

            sum_c_right_excluding_x = right_same - c2(rx)
            sum_c_left_excluding_x = left_same - c2(lx)

            for v in values:
                if v == x:
                    continue

                cl = left.get(v, 0)
                cr = right.get(v, 0)

                if cl:
                    # Extra x is on the left, v is the non-x chosen from the left.
                    f_right = c2(non_right - cr) - (sum_c_right_excluding_x - c2(cr))
                    sum_a += cl * f_right

                if cr:
                    # Extra x is on the right, v is the non-x chosen from the right.
                    f_left = c2(non_left - cl) - (sum_c_left_excluding_x - c2(cl))
                    sum_b += cr * f_left

            # x appears exactly twice and all other three values are distinct.
            good_eq2 = lx * sum_a + rx * sum_b

            ans = (ans + good_ge3 + good_eq2) % MOD

            left_same += lx
            left[x] = lx + 1

        return ans % MOD