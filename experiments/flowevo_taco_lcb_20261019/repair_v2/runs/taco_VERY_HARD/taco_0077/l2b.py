import sys
from collections import deque

sys.setrecursionlimit(1_000_000)


class Dinic:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, u, v, cap):
        self.g[u].append([v, cap, len(self.g[v])])
        self.g[v].append([u, 0, len(self.g[u]) - 1])

    def bfs(self, s, t):
        self.level = [-1] * self.n
        self.level[s] = 0
        q = deque([s])

        while q:
            u = q.popleft()
            for v, cap, rev in self.g[u]:
                if cap > 0 and self.level[v] == -1:
                    self.level[v] = self.level[u] + 1
                    q.append(v)

        return self.level[t] != -1

    def dfs(self, u, t, pushed):
        if u == t:
            return pushed

        while self.it[u] < len(self.g[u]):
            e = self.g[u][self.it[u]]
            v, cap, rev = e

            if cap > 0 and self.level[v] == self.level[u] + 1:
                flow = self.dfs(v, t, min(pushed, cap))
                if flow:
                    e[1] -= flow
                    self.g[v][rev][1] += flow
                    return flow

            self.it[u] += 1

        return 0

    def max_flow(self, s, t):
        total = 0
        INF = 10**18

        while self.bfs(s, t):
            self.it = [0] * self.n
            while True:
                flow = self.dfs(s, t, INF)
                if flow == 0:
                    break
                total += flow

        return total


def main():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx

        while idx < length and data[idx] <= 32:
            idx += 1

        sign = 1
        if data[idx] == 45:
            sign = -1
            idx += 1

        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return sign * num

    t = next_int()
    output = []

    for _ in range(t):
        H = next_int()
        W = next_int()
        N = next_int()

        grid = []
        for _ in range(H):
            row = [0] * W
            for j in range(W):
                row[j] = next_int()
            grid.append(row)

        ys = [0] * N
        xs = [0] * N
        abs_p = [0] * N
        h_value = [0] * N

        for i in range(N):
            y = next_int() - 1
            x = next_int() - 1
            p = next_int()

            ys[i] = y
            xs[i] = x
            abs_p[i] = p
            h_value[i] = grid[y][x]

        edges = []

        for i in range(N):
            for j in range(i + 1, N):
                if abs(ys[i] - ys[j]) + abs(xs[i] - xs[j]) == 1:
                    w = abs_p[i] * abs_p[j]
                    if w > 0:
                        edges.append((i, j, w))

        source = N
        sink = N + 1
        dinic = Dinic(N + 2)

        for i in range(N):
            b = abs_p[i] * h_value[i]
            c = 2 * b

            if c > 0:
                dinic.add_edge(source, i, c)
            elif c < 0:
                dinic.add_edge(i, sink, -c)

        for i, j, w in edges:
            cap = 2 * w
            dinic.add_edge(i, j, cap)
            dinic.add_edge(j, i, cap)

        dinic.max_flow(source, sink)

        reachable = [False] * (N + 2)
        reachable[source] = True
        stack = [source]

        while stack:
            u = stack.pop()
            for v, cap, rev in dinic.g[u]:
                if cap > 0 and not reachable[v]:
                    reachable[v] = True
                    stack.append(v)

        signs = [1] * N
        for i in range(N):
            if not reachable[i]:
                signs[i] = -1

        value = 0

        for i in range(N):
            value += signs[i] * abs_p[i] * h_value[i]

        for i, j, w in edges:
            value += signs[i] * signs[j] * w

        output.append(str(value))
        output.append(" ".join(map(str, signs)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()