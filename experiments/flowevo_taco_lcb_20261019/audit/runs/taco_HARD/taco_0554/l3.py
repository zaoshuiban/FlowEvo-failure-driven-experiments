import sys
from collections import deque


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, x = data[0], data[1], data[2]
    edges = []
    max_c = 0

    idx = 3
    for _ in range(m):
        a = data[idx] - 1
        b = data[idx + 1] - 1
        c = data[idx + 2]
        idx += 3
        edges.append((a, b, c))
        max_c = max(max_c, c)

    SCALE = 10 ** 9
    factors = [(a, b, c * x * SCALE) for a, b, c in edges]

    def feasible(S):
        # S = total_weight * SCALE
        g = [[] for _ in range(n)]
        to = []
        cap = []

        for u, v, factor in factors:
            val = factor // S  # floor(edge_capacity / (total_weight / x))
            if val <= 0:
                continue
            if val > x:
                val = x

            eid = len(to)
            g[u].append(eid)
            to.append(v)
            cap.append(val)

            g[v].append(eid + 1)
            to.append(u)
            cap.append(0)

        source = 0
        sink = n - 1
        flow = 0

        while flow < x:
            level = [-1] * n
            level[source] = 0
            q = deque([source])

            while q:
                v = q.popleft()
                next_level = level[v] + 1
                for eid in g[v]:
                    if cap[eid] > 0:
                        w = to[eid]
                        if level[w] == -1:
                            level[w] = next_level
                            q.append(w)

            if level[sink] == -1:
                break

            it = [0] * n

            def dfs(v, pushed):
                if v == sink:
                    return pushed

                gv = g[v]
                i = it[v]
                next_level = level[v] + 1

                while i < len(gv):
                    eid = gv[i]
                    w = to[eid]

                    if cap[eid] > 0 and level[w] == next_level:
                        sent = dfs(w, min(pushed, cap[eid]))
                        if sent:
                            cap[eid] -= sent
                            cap[eid ^ 1] += sent
                            it[v] = i
                            return sent

                    i += 1
                    it[v] = i

                return 0

            while flow < x:
                pushed = dfs(source, x - flow)
                if pushed == 0:
                    break
                flow += pushed
                if flow >= x:
                    return True

        return flow >= x

    lo = 0
    hi = x * max_c * SCALE + 1

    while hi - lo > 1:
        mid = (lo + hi) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid

    answer = lo / SCALE
    print(f"{answer:.10f}")


if __name__ == "__main__":
    solve()