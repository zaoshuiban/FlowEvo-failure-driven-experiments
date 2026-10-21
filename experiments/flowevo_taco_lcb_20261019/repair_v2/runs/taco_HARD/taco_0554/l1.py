import sys
from collections import deque

sys.setrecursionlimit(1_000_000)


class Dinic:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, u, v, cap):
        gu = self.g[u]
        gv = self.g[v]
        gu.append([v, cap, len(gv)])
        gv.append([u, 0, len(gu) - 1])

    def max_flow(self, s, t, limit):
        n = self.n
        g = self.g
        flow = 0

        while flow < limit:
            level = [-1] * n
            level[s] = 0
            q = deque([s])

            while q:
                v = q.popleft()
                for to, cap, rev in g[v]:
                    if cap > 0 and level[to] == -1:
                        level[to] = level[v] + 1
                        q.append(to)

            if level[t] == -1:
                break

            it = [0] * n

            def dfs(v, pushed):
                if v == t:
                    return pushed

                while it[v] < len(g[v]):
                    e = g[v][it[v]]
                    to, cap, rev = e

                    if cap > 0 and level[to] == level[v] + 1:
                        d = dfs(to, min(pushed, cap))
                        if d:
                            e[1] -= d
                            g[to][rev][1] += d
                            return d

                    it[v] += 1

                return 0

            while flow < limit:
                pushed = dfs(s, limit - flow)
                if pushed == 0:
                    break
                flow += pushed

        return flow


def solve():
    input = sys.stdin.readline

    n, m, x = map(int, input().split())
    edges = []

    for _ in range(m):
        a, b, c = map(int, input().split())
        edges.append((a - 1, b - 1, c))

    def feasible(weight):
        dinic = Dinic(n)

        for u, v, c in edges:
            cap = int(c / weight)
            if cap > x:
                cap = x
            if cap > 0:
                dinic.add_edge(u, v, cap)

        return dinic.max_flow(0, n - 1, x) >= x

    low = 0.0
    high = 1_000_001.0

    for _ in range(100):
        mid = (low + high) / 2.0
        if feasible(mid):
            low = mid
        else:
            high = mid

    answer = low * x
    print(f"{answer:.10f}")


if __name__ == "__main__":
    solve()