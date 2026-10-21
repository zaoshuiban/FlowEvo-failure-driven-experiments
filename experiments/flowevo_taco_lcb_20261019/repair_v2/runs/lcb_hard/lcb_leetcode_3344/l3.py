from typing import List

class Solution:
    def minimumDistance(self, points: List[List[int]]) -> int:
        n = len(points)
        INF = 10**30

        a_vals = [0] * n
        b_vals = [0] * n

        min_a = min_b = INF
        max_a = max_b = -INF

        min_a_idx = max_a_idx = min_b_idx = max_b_idx = 0

        for i, (x, y) in enumerate(points):
            a = x + y
            b = x - y

            a_vals[i] = a
            b_vals[i] = b

            if a < min_a:
                min_a = a
                min_a_idx = i
            if a > max_a:
                max_a = a
                max_a_idx = i
            if b < min_b:
                min_b = b
                min_b_idx = i
            if b > max_b:
                max_b = b
                max_b_idx = i

        candidates = {min_a_idx, max_a_idx, min_b_idx, max_b_idx}
        answer = INF

        for skip in candidates:
            cur_min_a = cur_min_b = INF
            cur_max_a = cur_max_b = -INF

            for i in range(n):
                if i == skip:
                    continue

                a = a_vals[i]
                b = b_vals[i]

                if a < cur_min_a:
                    cur_min_a = a
                if a > cur_max_a:
                    cur_max_a = a
                if b < cur_min_b:
                    cur_min_b = b
                if b > cur_max_b:
                    cur_max_b = b

            current_max_distance = max(
                cur_max_a - cur_min_a,
                cur_max_b - cur_min_b
            )
            answer = min(answer, current_max_distance)

        return answer