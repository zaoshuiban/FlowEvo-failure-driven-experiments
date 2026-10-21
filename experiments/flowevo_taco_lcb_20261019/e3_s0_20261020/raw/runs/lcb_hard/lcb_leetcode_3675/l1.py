from typing import List

class Solution:
    def maximizeSumOfWeights(self, edges: List[List[int]], k: int) -> int:
        n = len(edges) + 1
        adj = [[] for _ in range(n)]

        for u, v, w in edges:
            adj[u].append((v, w))
            adj[v].append((u, w))

        parent = [-1] * n
        order = [0]

        for u in order:
            for v, _ in adj[u]:
                if v == parent[u]:
                    continue
                parent[v] = u
                order.append(v)

        dp0 = [0] * n
        dp1 = [0] * n

        for u in reversed(order):
            base = 0
            gains = []

            for v, w in adj[u]:
                if parent[v] == u:
                    base += dp0[v]
                    gain = dp1[v] + w - dp0[v]
                    if gain > 0:
                        gains.append(gain)

            gains.sort(reverse=True)

            take0 = min(k, len(gains))
            sum0 = sum(gains[:take0])

            take1 = min(max(k - 1, 0), len(gains))
            sum1 = sum(gains[:take1])

            dp0[u] = base + sum0
            dp1[u] = base + sum1

        return dp0[0]