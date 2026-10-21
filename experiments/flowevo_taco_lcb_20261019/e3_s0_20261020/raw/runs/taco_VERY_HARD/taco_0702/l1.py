import sys


def solve():
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
        parent[0] = -2
        order = []
        stack = [0]

        while stack:
            v = stack.pop()
            order.append(v)
            for u in adj[v]:
                if u == parent[v]:
                    continue
                parent[u] = v
                stack.append(u)

        dp0 = [0] * n
        dp1 = [0] * n

        for v in reversed(order):
            base = 0
            best1 = 0
            best2 = 0

            for u in adj[v]:
                if parent[u] == v:
                    base += dp0[u]
                    gain = 1 + dp1[u] - dp0[u]

                    if gain > best1:
                        best2 = best1
                        best1 = gain
                    elif gain > best2:
                        best2 = gain

            dp0[v] = base + best1 + best2
            dp1[v] = base + best1

        kept_count = dp0[0]
        operations = (n - 1) - kept_count

        parent_kept = [False] * n
        kept_adj = [[] for _ in range(n)]

        for v in order:
            used_by_parent = 1 if v != 0 and parent_kept[v] else 0
            capacity = 2 - used_by_parent

            best1_gain = -1
            best1_u = -1
            best2_gain = -1
            best2_u = -1

            for u in adj[v]:
                if parent[u] == v:
                    gain = 1 + dp1[u] - dp0[u]

                    if gain > best1_gain:
                        best2_gain, best2_u = best1_gain, best1_u
                        best1_gain, best1_u = gain, u
                    elif gain > best2_gain:
                        best2_gain, best2_u = gain, u

            if capacity >= 1 and best1_gain > 0:
                u = best1_u
                parent_kept[u] = True
                kept_adj[v].append(u)
                kept_adj[u].append(v)

            if capacity >= 2 and best2_gain > 0:
                u = best2_u
                parent_kept[u] = True
                kept_adj[v].append(u)
                kept_adj[u].append(v)

        degree = [len(kept_adj[i]) for i in range(n)]
        visited = [False] * n
        components = []

        for start in range(n):
            if not visited[start] and degree[start] <= 1:
                component = []
                previous = -1
                current = start

                while True:
                    visited[current] = True
                    component.append(current)

                    nxt = -1
                    for neighbor in kept_adj[current]:
                        if neighbor != previous:
                            nxt = neighbor
                            break

                    if nxt == -1:
                        break

                    previous, current = current, nxt

                components.append(component)

        removed_edges = []
        for v in range(1, n):
            if not parent_kept[v]:
                removed_edges.append((parent[v] + 1, v + 1))

        output.append(str(operations))

        for i in range(operations):
            x1, y1 = removed_edges[i]
            x2 = components[i][-1] + 1
            y2 = components[i + 1][0] + 1
            output.append(f"{x1} {y1} {x2} {y2}")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()