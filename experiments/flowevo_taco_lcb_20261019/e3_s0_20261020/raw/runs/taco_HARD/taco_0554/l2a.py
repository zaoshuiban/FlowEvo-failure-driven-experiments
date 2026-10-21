import sys
from collections import deque

sys.setrecursionlimit(1_000_000)


class Dinic:
    __slots__ = ("n", "g")

    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, u, v, cap):
        g = self.g
        g[u].append([v, len(g[v]), cap])
        g[v].append([u, len(g[u]) - 1, 0])

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
                nxt_level = level[v] + 1
                for e in g[v]:
                    if e[2] > 0 and level[e[0]] == -1:
                        level[e[0]] = nxt_level
                        q.append(e[0])

            if level[t] == -1:
                break

            it = [0] * n

            def dfs(v, pushed):
                if v == t:
                    return pushed

                while it[v] < len(g[v]):
                    e = g[v][it[v]]

                    if e[2] > 0 and level[e[0]] == level[v] + 1:
                        tr = dfs(e[0], min(pushed, e[2]))
                        if tr:
                            e[2] -= tr
                            g[e[0]][e[1]][2] += tr
                            return tr

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

    n, m, x = data[0], data[1], data[2]
    edges = []
    max_cap = 0

    idx = 3
    for _ in range(m):
        a = data[idx] - 1
        b = data[idx + 1] - 1
        c = data[idx + 2]
        idx += 3
        edges.append((a, b, c))
        max_cap = max(max_cap, c)

    low = 0.0
    high = float(x * max_cap + 1)

    for _ in range(80):
        mid = (low + high) / 2.0

        dinic = Dinic(n)

        for a, b, c in edges:
            value = c * x / mid
            if value >= x:
                cap = x
            else:
                cap = int(value)

            if cap > 0:
                dinic.add_edge(a, b, cap)

        if dinic.max_flow(0, n - 1, x) >= x:
            low = mid
        else:
            high = mid

    print(f"{low:.12f}")


if __name__ == "__main__":
    solve()