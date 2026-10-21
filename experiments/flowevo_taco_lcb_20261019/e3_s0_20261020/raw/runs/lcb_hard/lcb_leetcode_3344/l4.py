from typing import List

class Solution:
    def minimumDistance(self, points: List[List[int]]) -> int:
        n = len(points)
        INF = 10**30

        a = [0] * n
        b = [0] * n

        min_a1 = min_a2 = INF
        max_a1 = max_a2 = -INF
        min_b1 = min_b2 = INF
        max_b1 = max_b2 = -INF

        min_a_idx = max_a_idx = min_b_idx = max_b_idx = -1

        for i, (x, y) in enumerate(points):
            av = x + y
            bv = x - y

            a[i] = av
            b[i] = bv

            if av < min_a1:
                min_a2 = min_a1
                min_a1 = av
                min_a_idx = i
            elif av < min_a2:
                min_a2 = av

            if av > max_a1:
                max_a2 = max_a1
                max_a1 = av
                max_a_idx = i
            elif av > max_a2:
                max_a2 = av

            if bv < min_b1:
                min_b2 = min_b1
                min_b1 = bv
                min_b_idx = i
            elif bv < min_b2:
                min_b2 = bv

            if bv > max_b1:
                max_b2 = max_b1
                max_b1 = bv
                max_b_idx = i
            elif bv > max_b2:
                max_b2 = bv

        answer = INF

        for i in range(n):
            cur_min_a = min_a2 if i == min_a_idx else min_a1
            cur_max_a = max_a2 if i == max_a_idx else max_a1

            cur_min_b = min_b2 if i == min_b_idx else min_b1
            cur_max_b = max_b2 if i == max_b_idx else max_b1

            current_max_distance = max(
                cur_max_a - cur_min_a,
                cur_max_b - cur_min_b
            )

            answer = min(answer, current_max_distance)

        return answer