import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ptr = 1
    output = []

    for _ in range(t):
        n = data[ptr]
        ptr += 1

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            a = data[ptr] - 1
            b = data[ptr + 1] - 1
            ptr += 2
            adj[a].append(b)
            adj[b].append(a)

        # Root the tree at vertex 0.
        parent = [-1] * n
        parent[0] = -2
        order = [0]
        qi = 0
        while qi < len(order):
            v = order[qi]
            qi += 1
            for u in adj[v]:
                if parent[u] == -1:
                    parent[u] = v
                    order.append(u)
        parent[0] = -1

        # dp0[v]: best in subtree if edge to parent is NOT kept.
        # dp1[v]: best in subtree if edge to parent IS kept.
        dp0 = [0] * n
        dp1 = [0] * n
        best1 = [-1] * n
        best2 = [-1] * n

        for v in reversed(order):
            base = 0
            b1 = -1
            b2 = -1
            g1 = 0
            g2 = 0

            for u in adj[v]:
                if parent[u] == v:
                    base += dp0[u]
                    gain = 1 + dp1[u] - dp0[u]

                    if gain > g1:
                        g2, g1 = g1, gain
                        b2, b1 = b1, u
                    elif gain > g2:
                        g2 = gain
                        b2 = u

            dp0[v] = base + (g1 if g1 > 0 else 0) + (g2 if g2 > 0 else 0)
            dp1[v] = base + (g1 if g1 > 0 else 0)

            if g1 > 0:
                best1[v] = b1
                if g2 > 0:
                    best2[v] = b2

        # Reconstruct which edges are kept in a maximum linear forest.
        kept_parent = [False] * n
        parent_kept = [False] * n

        for v in order:
            capacity = 2 - (1 if parent_kept[v] else 0)

            if capacity >= 1:
                u = best1[v]
                if u != -1:
                    kept_parent[u] = True
                    parent_kept[u] = True

            if capacity >= 2:
                u = best2[v]
                if u != -1:
                    kept_parent[u] = True
                    parent_kept[u] = True

        kept_adj = [[] for _ in range(n)]
        deleted = []

        for v in range(1, n):
            if kept_parent[v]:
                u = parent[v]
                kept_adj[v].append(u)
                kept_adj[u].append(v)
            else:
                deleted.append((v, parent[v]))

        # Find path components of the kept forest.
        visited = [False] * n
        components = []

        for start in range(n):
            if visited[start]:
                continue

            stack = [start]
            visited[start] = True
            endpoints = []

            while stack:
                v = stack.pop()

                if len(kept_adj[v]) <= 1:
                    endpoints.append(v)

                for u in kept_adj[v]:
                    if not visited[u]:
                        visited[u] = True
                        stack.append(u)

            if len(endpoints) == 1:
                components.append((endpoints[0], endpoints[0]))
            else:
                components.append((endpoints[0], endpoints[-1]))

        # Connect all components into one bamboo.
        connections = []
        if components:
            current = components[0][1]

            for i in range(1, len(components)):
                left, right = components[i]
                connections.append((current, left))
                current = right

        k = len(deleted)
        output.append(str(k))

        for i in range(k):
            x1, y1 = deleted[i]
            x2, y2 = connections[i]
            output.append(f"{x1 + 1} {y1 + 1} {x2 + 1} {y2 + 1}")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()