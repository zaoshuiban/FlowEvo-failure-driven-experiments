import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, u, v, cap):
        self.g[u].append([v, len(self.g[v]), cap])
        self.g[v].append([u, len(self.g[u]) - 1, 0])

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
                for to, rev, cap in g[v]:
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
                    to, rev, cap = e

                    if cap > 0 and level[to] == level[v] + 1:
                        pushed_next = min(pushed, cap)
                        got = dfs(to, pushed_next)

                        if got:
                            e[2] -= got
                            g[to][rev][2] += got
                            return got

                    it[v] += 1

                return 0

            while flow < limit:
                pushed = dfs(s, limit - flow)
                if pushed == 0:
                    break
                flow += pushed

        return flow


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)
    x = next(it)

    edges = []
    max_capacity = 0

    for _ in range(m):
        a = next(it) - 1
        b = next(it) - 1
        c = next(it)
        edges.append((a, b, c))
        max_capacity = max(max_capacity, c)

    def feasible(weight):
        dinic = Dinic(n)

        for u, v, c in edges:
            q = c / weight

            if q >= x:
                cap = x
            else:
                cap = int(q + 1e-12)

            if cap > 0:
                dinic.add_edge(u, v, cap)

        return dinic.max_flow(0, n - 1, x) >= x

    lo = 0.0
    hi = float(max_capacity)

    for _ in range(80):
        mid = (lo + hi) / 2.0

        if feasible(mid):
            lo = mid
        else:
            hi = mid

    answer = lo * x
    print(f"{answer:.10f}")


if __name__ == "__main__":
    solve()