import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    out = []

    for _ in range(t):
        n = next(it)

        adj = [[] for _ in range(n + 1)]
        U = [0] * n
        V = [0] * n

        for eid in range(1, n):
            a = next(it)
            b = next(it)
            U[eid] = a
            V[eid] = b
            adj[a].append((b, eid))
            adj[b].append((a, eid))

        parent = [0] * (n + 1)
        parent_edge = [0] * (n + 1)
        order = []

        stack = [1]
        parent[1] = -1

        while stack:
            u = stack.pop()
            order.append(u)

            for v, eid in adj[u]:
                if v == parent[u]:
                    continue
                parent[v] = u
                parent_edge[v] = eid
                stack.append(v)

        dp0 = [0] * (n + 1)
        dp1 = [0] * (n + 1)

        best1c = [0] * (n + 1)
        best1d = [0] * (n + 1)
        best2c = [0] * (n + 1)
        best2d = [0] * (n + 1)

        for u in reversed(order):
            base = 0
            b1c = b1d = 0
            b2c = b2d = 0

            for v, _ in adj[u]:
                if v == parent[u]:
                    continue

                base += dp0[v]
                delta = 1 + dp1[v] - dp0[v]

                if delta > b1d:
                    b2d, b2c = b1d, b1c
                    b1d, b1c = delta, v
                elif delta > b2d:
                    b2d, b2c = delta, v

            dp1[u] = base + b1d
            dp0[u] = base + b1d + b2d

            best1c[u] = b1c
            best1d[u] = b1d
            best2c[u] = b2c
            best2d[u] = b2d

        selected = [False] * n
        parent_selected = [False] * (n + 1)

        selected_count = 0

        for u in order:
            cap = 2 - (1 if parent_selected[u] else 0)

            if cap > 0 and best1d[u] > 0:
                v = best1c[u]
                eid = parent_edge[v]
                selected[eid] = True
                selected_count += 1
                parent_selected[v] = True
                cap -= 1

            if cap > 0 and best2d[u] > 0:
                v = best2c[u]
                eid = parent_edge[v]
                selected[eid] = True
                selected_count += 1
                parent_selected[v] = True
                cap -= 1

        removed_edges = []
        for eid in range(1, n):
            if not selected[eid]:
                removed_edges.append(eid)

        operations = len(removed_edges)
        out.append(str(operations))

        if operations == 0:
            continue

        kept_degree = [0] * (n + 1)

        for eid in range(1, n):
            if selected[eid]:
                a = U[eid]
                b = V[eid]
                kept_degree[a] += 1
                kept_degree[b] += 1

        visited = [False] * (n + 1)
        components = []

        for start in range(1, n + 1):
            if visited[start]:
                continue

            visited[start] = True
            stack = [start]
            endpoints = []

            while stack:
                u = stack.pop()

                if kept_degree[u] <= 1:
                    endpoints.append(u)

                for v, eid in adj[u]:
                    if selected[eid] and not visited[v]:
                        visited[v] = True
                        stack.append(v)

            if len(endpoints) == 1:
                components.append((endpoints[0], endpoints[0]))
            else:
                components.append((endpoints[0], endpoints[1]))

        for i in range(operations):
            eid = removed_edges[i]
            a = U[eid]
            b = V[eid]

            c = components[i][1]
            d = components[i + 1][0]

            out.append(f"{a} {b} {c} {d}")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()