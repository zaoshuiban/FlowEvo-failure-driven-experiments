import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    m = next(it)
    c = [next(it) for _ in range(n)]

    a = [0] * m
    b = [0] * m
    adj = [[] for _ in range(n)]

    for eid in range(m):
        u = next(it) - 1
        v = next(it) - 1
        a[eid] = u
        b[eid] = v
        adj[u].append((v, eid))
        adj[v].append((u, eid))

    parent = [-1] * n
    parent_edge = [-1] * n
    color = [-1] * n
    tree_edge = [False] * m
    order = []

    parent[0] = -2
    color[0] = 0
    order.append(0)
    q = deque([0])

    while q:
        v = q.popleft()
        for to, eid in adj[v]:
            if parent[to] == -1:
                parent[to] = v
                parent_edge[to] = eid
                color[to] = color[v] ^ 1
                tree_edge[eid] = True
                order.append(to)
                q.append(to)

    special = -1
    for eid in range(m):
        if not tree_edge[eid] and color[a[eid]] == color[b[eid]]:
            special = eid
            break

    const_w = [0] * m
    coef_w = [0] * m

    for v in reversed(order):
        if v == 0:
            continue

        s_const = 0
        s_coef = 0

        for to, eid in adj[v]:
            if eid == parent_edge[v]:
                continue

            if tree_edge[eid]:
                s_const += const_w[eid]
                s_coef += coef_w[eid]
            elif eid == special:
                s_coef += 1

        pe = parent_edge[v]
        const_w[pe] = c[v] - s_const
        coef_w[pe] = -s_coef

    root_const = 0
    root_coef = 0

    for to, eid in adj[0]:
        if tree_edge[eid]:
            root_const += const_w[eid]
            root_coef += coef_w[eid]
        elif eid == special:
            root_coef += 1

    if root_coef == 0:
        if root_const != c[0]:
            print("NO")
            return
        t = 0
    else:
        numerator = c[0] - root_const
        if numerator % root_coef != 0:
            print("NO")
            return
        t = numerator // root_coef

    ans = [0] * m

    for eid in range(m):
        if tree_edge[eid]:
            ans[eid] = const_w[eid] + coef_w[eid] * t

    if special != -1:
        ans[special] = t

    out = ["YES"]
    out.extend(map(str, ans))
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()