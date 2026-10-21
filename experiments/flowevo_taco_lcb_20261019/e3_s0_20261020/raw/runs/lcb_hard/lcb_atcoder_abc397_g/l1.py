import sys
from collections import deque

sys.setrecursionlimit(1 << 20)


class Dinic:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, fr, to, cap):
        g = self.g
        g[fr].append([to, cap, len(g[to])])
        g[to].append([fr, 0, len(g[fr]) - 1])

    def max_flow(self, s, t, limit=10**18):
        n = self.n
        g = self.g
        flow = 0

        while flow < limit:
            level = [-1] * n
            level[s] = 0
            q = deque([s])

            while q:
                v = q.popleft()
                for e in g[v]:
                    if e[1] > 0 and level[e[0]] < 0:
                        level[e[0]] = level[v] + 1
                        q.append(e[0])

            if level[t] < 0:
                break

            it = [0] * n

            def dfs(v, f):
                if v == t:
                    return f

                while it[v] < len(g[v]):
                    e = g[v][it[v]]
                    if e[1] > 0 and level[e[0]] == level[v] + 1:
                        ret = dfs(e[0], min(f, e[1]))
                        if ret:
                            e[1] -= ret
                            g[e[0]][e[2]][1] += ret
                            return ret
                    it[v] += 1

                return 0

            while flow < limit:
                f = dfs(s, limit - flow)
                if f == 0:
                    break
                flow += f

        return flow


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N, M, K = data[0], data[1], data[2]

    edges = []
    idx = 3
    for _ in range(M):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        edges.append((u, v))

    INF = 10**9

    def feasible(D):
        if D == 0:
            return True

        node_count = N * D
        source = node_count
        sink = node_count + 1
        dinic = Dinic(node_count + 2)

        def node(v, i):
            # i is 1-indexed: 1 <= i <= D
            return v * D + (i - 1)

        # Monotonicity: h[v] >= i implies h[v] >= i-1
        for v in range(N):
            for i in range(2, D + 1):
                dinic.add_edge(node(v, i), node(v, i - 1), INF)

        for u, v in edges:
            # Cost 1 if h[v] = h[u] + 1
            for i in range(1, D + 1):
                dinic.add_edge(node(v, i), node(u, i), 1)

            # Constraint: h[v] <= h[u] + 1
            for i in range(2, D + 1):
                dinic.add_edge(node(v, i), node(u, i - 1), INF)

        # h[0] = 0
        for i in range(1, D + 1):
            dinic.add_edge(node(0, i), sink, INF)

        # h[N-1] = D
        for i in range(1, D + 1):
            dinic.add_edge(source, node(N - 1, i), INF)

        flow = dinic.max_flow(source, sink, K + 1)
        return flow <= K

    low = 0
    high = N  # high is always infeasible

    while high - low > 1:
        mid = (low + high) // 2
        if feasible(mid):
            low = mid
        else:
            high = mid

    print(low)


if __name__ == "__main__":
    main()