import sys
from collections import deque
from array import array


class Dinic:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, u, v, cap):
        gu = self.g[u]
        gv = self.g[v]
        gu.append([v, len(gv), cap])
        gv.append([u, len(gu) - 1, 0])

    def max_flow(self, s, t):
        flow = 0
        n = self.n
        g = self.g
        INF = 10**18

        while True:
            level = [-1] * n
            level[s] = 0
            q = deque([s])

            while q:
                u = q.popleft()
                for v, rev, cap in g[u]:
                    if cap > 0 and level[v] == -1:
                        level[v] = level[u] + 1
                        q.append(v)

            if level[t] == -1:
                break

            it = [0] * n

            def dfs(u, pushed):
                if u == t:
                    return pushed

                while it[u] < len(g[u]):
                    i = it[u]
                    v, rev, cap = g[u][i]

                    if cap > 0 and level[v] == level[u] + 1:
                        sent = dfs(v, min(pushed, cap))
                        if sent:
                            g[u][i][2] -= sent
                            g[v][rev][2] += sent
                            return sent

                    it[u] += 1

                return 0

            while True:
                pushed = dfs(s, INF)
                if pushed == 0:
                    break
                flow += pushed

        return flow

    def reachable_from(self, s):
        seen = [False] * self.n
        seen[s] = True
        q = deque([s])

        while q:
            u = q.popleft()
            for v, rev, cap in self.g[u]:
                if cap > 0 and not seen[v]:
                    seen[v] = True
                    q.append(v)

        return seen


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx

        while idx < length and data[idx] <= 32:
            idx += 1

        sign = 1
        if data[idx] == 45:  # '-'
            sign = -1
            idx += 1

        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return sign * num

    T = next_int()
    output = []

    for _ in range(T):
        H = next_int()
        W = next_int()
        N = next_int()

        grid = array('i')
        for _ in range(H * W):
            grid.append(next_int())

        ys = [0] * N
        xs = [0] * N
        vals = [0] * N
        hs = [0] * N

        for i in range(N):
            y = next_int() - 1
            x = next_int() - 1
            a = next_int()

            ys[i] = y
            xs[i] = x
            vals[i] = a
            hs[i] = grid[y * W + x]

        source = N
        sink = N + 1
        dinic = Dinic(N + 2)

        for i in range(N):
            # c_i = -2 * |p_i| * h_{y_i, x_i}
            c = -2 * vals[i] * hs[i]

            if c > 0:
                dinic.add_edge(i, sink, c)
            elif c < 0:
                dinic.add_edge(source, i, -c)

        edges = []

        for i in range(N):
            for j in range(i + 1, N):
                if abs(ys[i] - ys[j]) + abs(xs[i] - xs[j]) == 1:
                    edges.append((i, j))

                    cap = 2 * vals[i] * vals[j]
                    if cap > 0:
                        dinic.add_edge(i, j, cap)
                        dinic.add_edge(j, i, cap)

        dinic.max_flow(source, sink)
        reachable = dinic.reachable_from(source)

        p = [0] * N
        signs = []

        for i in range(N):
            if vals[i] == 0:
                signs.append(1)
                p[i] = 0
            elif reachable[i]:
                signs.append(1)
                p[i] = vals[i]
            else:
                signs.append(-1)
                p[i] = -vals[i]

        answer = 0

        for i in range(N):
            answer += p[i] * hs[i]

        for i, j in edges:
            answer += p[i] * p[j]

        output.append(str(answer))
        output.append(" ".join(map(str, signs)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()