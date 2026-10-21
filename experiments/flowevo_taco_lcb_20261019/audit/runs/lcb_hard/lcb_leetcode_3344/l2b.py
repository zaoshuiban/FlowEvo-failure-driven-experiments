from typing import List

class Solution:
    def minimumDistance(self, points: List[List[int]]) -> int:
        min_a = min_b = 10**30
        max_a = max_b = -10**30

        min_ai = max_ai = min_bi = max_bi = 0

        for i, (x, y) in enumerate(points):
            a = x + y
            b = x - y

            if a < min_a:
                min_a = a
                min_ai = i
            if a > max_a:
                max_a = a
                max_ai = i
            if b < min_b:
                min_b = b
                min_bi = i
            if b > max_b:
                max_b = b
                max_bi = i

        candidates = {min_ai, max_ai, min_bi, max_bi}
        answer = 10**30

        for skip in candidates:
            cur_min_a = cur_min_b = 10**30
            cur_max_a = cur_max_b = -10**30

            for i, (x, y) in enumerate(points):
                if i == skip:
                    continue

                a = x + y
                b = x - y

                cur_min_a = min(cur_min_a, a)
                cur_max_a = max(cur_max_a, a)
                cur_min_b = min(cur_min_b, b)
                cur_max_b = max(cur_max_b, b)

            distance = max(cur_max_a - cur_min_a, cur_max_b - cur_min_b)
            answer = min(answer, distance)

        return answer