from typing import List

class Solution:
    def minimumDistance(self, points: List[List[int]]) -> int:
        n = len(points)
        u = [0] * n
        v = [0] * n

        for i, (x, y) in enumerate(points):
            u[i] = x + y
            v[i] = x - y

        INF = 10**30

        pre_min_u = [INF] * (n + 1)
        pre_max_u = [-INF] * (n + 1)
        pre_min_v = [INF] * (n + 1)
        pre_max_v = [-INF] * (n + 1)

        for i in range(n):
            pre_min_u[i + 1] = min(pre_min_u[i], u[i])
            pre_max_u[i + 1] = max(pre_max_u[i], u[i])
            pre_min_v[i + 1] = min(pre_min_v[i], v[i])
            pre_max_v[i + 1] = max(pre_max_v[i], v[i])

        suf_min_u = [INF] * (n + 1)
        suf_max_u = [-INF] * (n + 1)
        suf_min_v = [INF] * (n + 1)
        suf_max_v = [-INF] * (n + 1)

        for i in range(n - 1, -1, -1):
            suf_min_u[i] = min(suf_min_u[i + 1], u[i])
            suf_max_u[i] = max(suf_max_u[i + 1], u[i])
            suf_min_v[i] = min(suf_min_v[i + 1], v[i])
            suf_max_v[i] = max(suf_max_v[i + 1], v[i])

        answer = INF

        for i in range(n):
            min_u = min(pre_min_u[i], suf_min_u[i + 1])
            max_u = max(pre_max_u[i], suf_max_u[i + 1])
            min_v = min(pre_min_v[i], suf_min_v[i + 1])
            max_v = max(pre_max_v[i], suf_max_v[i + 1])

            current = max(max_u - min_u, max_v - min_v)
            answer = min(answer, current)

        return answer