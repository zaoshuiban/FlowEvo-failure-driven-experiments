import sys
from collections import deque
from array import array

sys.setrecursionlimit(1_000_000)


class Dinic:
    def __init__(self, n):
        self.n = n
        self.g = [[] for _ in range(n)]

    def add_edge(self, fr, to, cap):
        g = self.g
        g[fr].append([to, len(g[to]), cap])
        g[to].append([fr, len(g[fr]) - 1, 0])

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
                v = q.popleft()
                for e in g[v]:
                    if e[2] > 0 and level[e[0]] == -1:
                        level[e[0]] = level[v] + 1
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

            while True:
                pushed = dfs(s, INF)
                if not pushed:
                    break
                flow += pushed

        return flow

    def reachable_from(self, s):
        n = self.n
        g = self.g
        vis = [False] * n
        vis[s] = True
        q = deque([s])

        while q:
            v = q.popleft()
            for e in g[v]:
                if e[2] > 0 and not vis[e[0]]:
                    vis[e[0]] = True
                    q.append(e[0])

        return vis


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
        h = next_int()
        w = next_int()
        n = next_int()

        grid = array('h')
        for _ in range(h * w):
            grid.append(next_int())

        ys = []
        xs = []
        a = []
        c = []
        pos = {}

        for i in range(n):
            y = next_int() - 1
            x = next_int() - 1
            p = abs(next_int())

            ys.append(y)
            xs.append(x)
            a.append(p)

            c.append(p * grid[y * w + x])
            pos[(y, x)] = i

        edges = []
        sum_w = 0

        for i in range(n):
            y = ys[i]
            x = xs[i]

            for dy, dx in ((1, 0), (0, 1)):
                j = pos.get((y + dy, x + dx))
                if j is not None:
                    weight = a[i] * a[j]
                    edges.append((i, j, weight))
                    sum_w += weight

        source = n
        sink = n + 1
        dinic = Dinic(n + 2)

        beta_sum = 0

        for i, ci in enumerate(c):
            val = 2 * ci

            if val > 0:
                dinic.add_edge(source, i, val)
            elif val < 0:
                dinic.add_edge(i, sink, -val)
                beta_sum += -val

        for u, v, weight in edges:
            cap = 2 * weight
            dinic.add_edge(u, v, cap)
            dinic.add_edge(v, u, cap)

        min_cut = dinic.max_flow(source, sink)
        constant = sum(c) + sum_w

        answer = constant + beta_sum - min_cut

        reachable = dinic.reachable_from(source)
        signs = []

        for i in range(n):
            signs.append('1' if reachable[i] else '-1')

        output.append(str(answer))
        output.append(' '.join(signs))

    sys.stdout.write('\n'.join(output))


if __name__ == "__main__":
    main()