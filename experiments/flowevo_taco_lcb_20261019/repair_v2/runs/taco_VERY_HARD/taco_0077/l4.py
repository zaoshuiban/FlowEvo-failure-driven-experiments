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
        gu.append([v, len(gv), cap])
        gv.append([u, len(gu) - 1, 0])

    def max_flow(self, s, t):
        n = self.n
        g = self.g
        flow = 0
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
                    e = g[u][it[u]]
                    v, rev, cap = e

                    if cap > 0 and level[v] == level[u] + 1:
                        got = dfs(v, min(pushed, cap))
                        if got:
                            e[2] -= got
                            g[v][rev][2] += got
                            return got

                    it[u] += 1

                return 0

            while True:
                pushed = dfs(s, INF)
                if pushed == 0:
                    break
                flow += pushed

        return flow


def main():
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
    answers = []

    for _ in range(T):
        H = next_int()
        W = next_int()
        N = next_int()

        total_cells = H * W
        grid = [0] * total_cells

        for i in range(total_cells):
            grid[i] = next_int()

        ys = [0] * N
        xs = [0] * N
        abs_p = [0] * N
        linear = [0] * N

        for i in range(N):
            y = next_int() - 1
            x = next_int() - 1
            p = next_int()

            ys[i] = y
            xs[i] = x
            abs_p[i] = p
            linear[i] = p * grid[y * W + x]

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
            b = linear[i]
            if b > 0:
                dinic.add_edge(source, i, 2 * b)
            elif b < 0:
                dinic.add_edge(i, sink, -2 * b)

        for i, j, w in edges:
            cap = 2 * w
            dinic.add_edge(i, j, cap)
            dinic.add_edge(j, i, cap)

        dinic.max_flow(source, sink)

        reachable = [False] * (N + 2)
        reachable[source] = True
        stack = [source]

        g = dinic.g

        while stack:
            u = stack.pop()
            for v, rev, cap in g[u]:
                if cap > 0 and not reachable[v]:
                    reachable[v] = True
                    stack.append(v)

        signs = [1] * N
        for i in range(N):
            if not reachable[i]:
                signs[i] = -1

        answer_value = 0

        for i in range(N):
            answer_value += signs[i] * abs_p[i] * grid[ys[i] * W + xs[i]]

        for i, j, w in edges:
            answer_value += signs[i] * signs[j] * w

        answers.append(str(answer_value))
        answers.append(" ".join(map(str, signs)))

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()