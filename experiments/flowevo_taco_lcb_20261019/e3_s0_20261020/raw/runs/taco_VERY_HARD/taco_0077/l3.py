import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        self.ad = [[] for _ in range(n)]

    def add_edge(self, u, v, cap):
        self.ad[u].append([v, cap, len(self.ad[v])])
        self.ad[v].append([u, 0, len(self.ad[u]) - 1])

    def max_flow(self, s, t):
        flow = 0
        INF = 10**18
        n = self.n

        while True:
            level = [-1] * n
            level[s] = 0
            q = deque([s])

            while q:
                u = q.popleft()
                for v, cap, rev in self.ad[u]:
                    if cap > 0 and level[v] == -1:
                        level[v] = level[u] + 1
                        q.append(v)

            if level[t] == -1:
                break

            it = [0] * n

            def dfs(u, pushed):
                if u == t:
                    return pushed

                while it[u] < len(self.ad[u]):
                    e = self.ad[u][it[u]]
                    v, cap, rev = e

                    if cap > 0 and level[v] == level[u] + 1:
                        got = dfs(v, min(pushed, cap))
                        if got:
                            e[1] -= got
                            self.ad[v][rev][1] += got
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
    out = []

    for _ in range(T):
        H = next_int()
        W = next_int()
        N = next_int()

        total_cells = H * W
        grid = [0] * total_cells
        for k in range(total_cells):
            grid[k] = next_int()

        ys = [0] * N
        xs = [0] * N
        ap = [0] * N
        hv = [0] * N
        pos_to_idx = {}

        for i in range(N):
            y = next_int() - 1
            x = next_int() - 1
            p = next_int()

            ys[i] = y
            xs[i] = x
            ap[i] = p
            hv[i] = grid[y * W + x]
            pos_to_idx[(y, x)] = i

        edges = []
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))

        for i in range(N):
            y = ys[i]
            x = xs[i]

            for dy, dx in dirs:
                j = pos_to_idx.get((y + dy, x + dx))
                if j is not None and i < j:
                    w = ap[i] * ap[j]
                    if w > 0:
                        edges.append((i, j, w))

        source = N
        sink = N + 1
        dinic = Dinic(N + 2)

        for i in range(N):
            b = ap[i] * hv[i]
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

        while stack:
            u = stack.pop()
            for v, cap, rev in dinic.ad[u]:
                if cap > 0 and not reachable[v]:
                    reachable[v] = True
                    stack.append(v)

        signs = [1] * N
        for i in range(N):
            if not reachable[i]:
                signs[i] = -1

        value = 0
        for i in range(N):
            value += signs[i] * ap[i] * hv[i]

        for i, j, w in edges:
            value += signs[i] * signs[j] * w

        out.append(str(value))
        out.append(" ".join(map(str, signs)))

    sys.stdout.write("\n".join(out))
    if out:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()