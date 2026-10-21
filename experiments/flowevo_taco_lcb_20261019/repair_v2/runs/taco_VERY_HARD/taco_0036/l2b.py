import sys
from collections import deque


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

    q = deque([0])
    parent[0] = 0
    color[0] = 0

    while q:
        v = q.popleft()
        order.append(v)

        for to, eid in adj[v]:
            if parent[to] == -1:
                parent[to] = v
                parent_edge[to] = eid
                color[to] = color[v] ^ 1
                in_tree[eid] = True
                q.append(to)

    balance_side = 0
    for i in range(n):
        if color[i] == 0:
            balance_side += c[i]
        else:
            balance_side -= c[i]

    conflict_edge = -1
    for eid, (a, b) in enumerate(edges):
        if not in_tree[eid] and color[a] == color[b]:
            conflict_edge = eid
            break

    weights = [0] * m

    def solve_tree(cvals):
        bal = cvals.copy()

        for v in reversed(order):
            if v == 0:
                continue

            w = bal[v]
            weights[parent_edge[v]] = w
            bal[parent[v]] -= w

        return bal[0] == 0

    if conflict_edge == -1:
        if balance_side != 0:
            print("NO")
            return

        if not solve_tree(c):
            print("NO")
            return

    else:
        u, v = edges[conflict_edge]

        if balance_side % 2 != 0:
            print("NO")
            return

        if color[u] == 0:
            w = balance_side // 2
        else:
            w = -(balance_side // 2)

        cprime = c.copy()
        cprime[u] -= w
        cprime[v] -= w

        weights[conflict_edge] = w

        if not solve_tree(cprime):
            print("NO")
            return

    ans = ["YES"]
    ans.extend(str(w) for w in weights)
    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    main()