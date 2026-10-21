import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    output = []

    for _ in range(t):
        n = next(it)
        adj = [[] for _ in range(n)]

        for _ in range(n - 1):
            a = next(it) - 1
            b = next(it) - 1
            adj[a].append(b)
            adj[b].append(a)

        parent = [-1] * n
        order = [0]

        for v in order:
            for u in adj[v]:
                if u == parent[v]:
                    continue
                parent[u] = v
                order.append(u)

        dp0 = [0] * n  # parent edge is not selected
        dp1 = [0] * n  # parent edge is selected

        for v in reversed(order):
            base = 0
            good = 0

            for u in adj[v]:
                if parent[u] == v:
                    base += dp0[u]
                    if dp0[u] == dp1[u]:
                        good += 1

            dp0[v] = base + min(2, good)
            dp1[v] = base + min(1, good)

        selected_child = [False] * n

        for v in order:
            parent_selected = 1 if selected_child[v] else 0
            capacity = 2 - parent_selected
            taken = 0

            for u in adj[v]:
                if parent[u] == v:
                    if dp0[u] == dp1[u] and taken < capacity:
                        selected_child[u] = True
                        taken += 1
                    else:
                        selected_child[u] = False

        selected_adj = [[] for _ in range(n)]
        removed = []

        for v in range(1, n):
            p = parent[v]
            if selected_child[v]:
                selected_adj[v].append(p)
                selected_adj[p].append(v)
            else:
                removed.append((p, v))

        visited = [False] * n
        components = []

        for start_vertex in range(n):
            if visited[start_vertex]:
                continue

            stack = [start_vertex]
            visited[start_vertex] = True
            comp = []

            while stack:
                v = stack.pop()
                comp.append(v)

                for u in selected_adj[v]:
                    if not visited[u]:
                        visited[u] = True
                        stack.append(u)

            if len(comp) == 1:
                components.append((start_vertex, start_vertex))
            else:
                endpoints = []
                for v in comp:
                    if len(selected_adj[v]) <= 1:
                        endpoints.append(v)
                components.append((endpoints[0], endpoints[1]))

        added = []
        for i in range(len(components) - 1):
            added.append((components[i][1], components[i + 1][0]))

        k = len(removed)
        output.append(str(k))

        for i in range(k):
            x1, y1 = removed[i]
            x2, y2 = added[i]
            output.append(f"{x1 + 1} {y1 + 1} {x2 + 1} {y2 + 1}")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()