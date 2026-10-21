import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    c = [next(it) for _ in range(n)]

    edges = []
    adj = [[] for _ in range(n)]

    for eid in range(m):
        a = next(it) - 1
        b = next(it) - 1
        edges.append((a, b))
        adj[a].append((b, eid))
        adj[b].append((a, eid))

    parent = [-1] * n
    parent_edge = [-1] * n
    color = [-1] * n
    in_tree = [False] * m
    order = []

    # Build any spanning tree using iterative DFS.
    stack = [0]
    parent[0] = 0
    color[0] = 0

    while stack:
        v = stack.pop()
        order.append(v)

        for to, eid in adj[v]:
            if parent[to] == -1:
                parent[to] = v
                parent_edge[to] = eid
                color[to] = color[v] ^ 1
                in_tree[eid] = True
                stack.append(to)

    # Signed sum with respect to the tree bipartition.
    balance_side = 0
    for v in range(n):
        if color[v] == 0:
            balance_side += c[v]
        else:
            balance_side -= c[v]

    # Find a non-tree edge whose endpoints have the same color.
    # Such an edge exists iff the graph is non-bipartite.
    conflict_edge = -1
    for eid, (a, b) in enumerate(edges):
        if not in_tree[eid] and color[a] == color[b]:
            conflict_edge = eid
            break

    weights = [0] * m

    def solve_tree(values):
        bal = values[:]

        for v in reversed(order):
            if v == 0:
                continue

            w = bal[v]
            weights[parent_edge[v]] = w
            bal[parent[v]] -= w

        return bal[0] == 0

    if conflict_edge == -1:
        # Graph is bipartite.
        if balance_side != 0:
            sys.stdout.write("NO\n")
            return

        if not solve_tree(c):
            sys.stdout.write("NO\n")
            return
    else:
        # Graph is non-bipartite.
        if balance_side % 2 != 0:
            sys.stdout.write("NO\n")
            return

        u, v = edges[conflict_edge]

        # sign = +1 for color 0, -1 for color 1
        sign = 1 if color[u] == 0 else -1
        w = (balance_side // 2) * sign

        cprime = c[:]
        cprime[u] -= w
        cprime[v] -= w

        weights[conflict_edge] = w

        if not solve_tree(cprime):
            sys.stdout.write("NO\n")
            return

    out = ["YES"]
    out.extend(str(w) for w in weights)
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()