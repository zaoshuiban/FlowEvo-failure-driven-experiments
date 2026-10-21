from typing import List

class Solution:
    def minimumDistance(self, points: List[List[int]]) -> int:
        n = len(points)
        u = [x + y for x, y in points]
        v = [x - y for x, y in points]

        min_u, max_u = min(u), max(u)
        min_v, max_v = min(v), max(v)

        candidates = {
            u.index(min_u),
            u.index(max_u),
            v.index(min_v),
            v.index(max_v),
        }

        ans = float("inf")

        for skip in candidates:
            cur_min_u = cur_min_v = float("inf")
            cur_max_u = cur_max_v = float("-inf")

            for i in range(n):
                if i == skip:
                    continue

                cur_min_u = min(cur_min_u, u[i])
                cur_max_u = max(cur_max_u, u[i])
                cur_min_v = min(cur_min_v, v[i])
                cur_max_v = max(cur_max_v, v[i])

            current = max(cur_max_u - cur_min_u, cur_max_v - cur_min_v)
            ans = min(ans, current)

        return int(ans)