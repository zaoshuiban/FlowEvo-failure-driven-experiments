import sys

INF = 1 << 62
SMALL = 60


def solve_small(n, adj, A):
    parent = [0] * (n + 1)
    parent[1] = -1
    children = [[] for _ in range(n + 1)]
    order = [1]

    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                children[u].append(v)
                order.append(v)

    ans = [-1] * (n + 1)
    subvals = [None] * (n + 1)

    for u in reversed(order):
        arr = [A[u]]
        for v in children[u]:
            arr.extend(subvals[v])
        subvals[u] = arr

        if len(arr) >= 2:
            arr.sort()
            mn = INF
            prev = arr[0]
            for i in range(1, len(arr)):
                x = prev ^ arr[i]
                if x < mn:
                    mn = x
                prev = arr[i]
            ans[u] = mn

    return " ".join(str(ans[i]) for i in range(1, n + 1))


def solve_large(n, adj, A):
    parent = [0] * (n + 1)
    parent[1] = -1
    order = [1]

    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)

    size = [1] * (n + 1)
    heavy = [0] * (n + 1)

    for u in reversed(order):
        total = 1
        best_size = 0
        hv = 0
        for v in adj[u]:
            if parent[v] == u:
                total += size[v]
                if size[v] > best_size:
                    best_size = size[v]
                    hv = v
        size[u] = total
        heavy[u] = hv

    tin = [0] * (n + 1)
    tout = [0] * (n + 1)
    euler = [0] * n
    timer = 0

    stack = [(1, 0)]
    while stack:
        u, state = stack.pop()
        if state == 0:
            tin[u] = timer
            euler[timer] = u
            timer += 1

            stack.append((u, 1))
            for v in reversed(adj[u]):
                if v != parent[u]:
                    stack.append((v, 0))
        else:
            tout[u] = timer

    values = sorted(set(A[1:]))
    m = len(values)
    val_to_idx = {v: i for i, v in enumerate(values)}

    node_idx = [0] * (n + 1)
    for i in range(1, n + 1):
        node_idx[i] = val_to_idx[A[i]]

    seg_n = 1
    while seg_n < m:
        seg_n <<= 1

    first = [-1] * (2 * seg_n)
    last = [-1] * (2 * seg_n)
    best = [INF] * (2 * seg_n)

    cnt = [0] * m
    duplicate_count = 0

    def add_node(
        u,
        first=first,
        last=last,
        best=best,
        cnt=cnt,
        node_idx=node_idx,
        values=values,
        seg_n=seg_n,
        INF=INF,
    ):
        nonlocal duplicate_count

        idx = node_idx[u]
        c = cnt[idx]

        if c == 0:
            val = values[idx]
            p = seg_n + idx
            first[p] = val
            last[p] = val
            best[p] = INF

            p >>= 1
            while p:
                lc = p << 1
                rc = lc | 1

                lf = first[lc]
                rf = first[rc]

                if lf == -1:
                    first[p] = rf
                    last[p] = last[rc]
                    best[p] = best[rc]
                elif rf == -1:
                    first[p] = lf
                    last[p] = last[lc]
                    best[p] = best[lc]
                else:
                    first[p] = lf
                    last[p] = last[rc]

                    b = best[lc]
                    br = best[rc]
                    if br < b:
                        b = br

                    cross = last[lc] ^ rf
                    if cross < b:
                        b = cross

                    best[p] = b

                p >>= 1

            cnt[idx] = 1
        else:
            if c == 1:
                duplicate_count += 1
            cnt[idx] = c + 1

    def remove_node(
        u,
        first=first,
        last=last,
        best=best,
        cnt=cnt,
        node_idx=node_idx,
        seg_n=seg_n,
        INF=INF,
    ):
        nonlocal duplicate_count

        idx = node_idx[u]
        c = cnt[idx]

        if c == 1:
            p = seg_n + idx
            first[p] = -1
            last[p] = -1
            best[p] = INF

            p >>= 1
            while p:
                lc = p << 1
                rc = lc | 1

                lf = first[lc]
                rf = first[rc]

                if lf == -1:
                    first[p] = rf
                    last[p] = last[rc]
                    best[p] = best[rc]
                elif rf == -1:
                    first[p] = lf
                    last[p] = last[lc]
                    best[p] = best[lc]
                else:
                    first[p] = lf
                    last[p] = last[rc]

                    b = best[lc]
                    br = best[rc]
                    if br < b:
                        b = br

                    cross = last[lc] ^ rf
                    if cross < b:
                        b = cross

                    best[p] = b

                p >>= 1

            cnt[idx] = 0
        else:
            if c == 2:
                duplicate_count -= 1
            cnt[idx] = c - 1

    ans = [-1] * (n + 1)
    events = [(0, 1, 0)]

    while events:
        typ, u, keep = events.pop()

        if typ == 0:
            events.append((1, u, keep))

            hv = heavy[u]
            if hv:
                events.append((0, hv, 1))

            for v in adj[u]:
                if parent[v] == u and v != hv:
                    events.append((0, v, 0))

        else:
            hv = heavy[u]

            for v in adj[u]:
                if parent[v] == u and v != hv:
                    for pos in range(tin[v], tout[v]):
                        add_node(euler[pos])

            add_node(u)

            if size[u] >= 2:
                if duplicate_count > 0:
                    ans[u] = 0
                else:
                    ans[u] = best[1]
            else:
                ans[u] = -1

            if not keep:
                for pos in range(tin[u], tout[u]):
                    remove_node(euler[pos])

    return " ".join(str(ans[i]) for i in range(1, n + 1))


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        if n == 1:
            idx += 1
            output.append("-1")
            continue

        adj = [[] for _ in range(n + 1)]

        for _ in range(n - 1):
            u = data[idx]
            v = data[idx + 1]
            idx += 2
            adj[u].append(v)
            adj[v].append(u)

        A = [0] * (n + 1)
        for i in range(1, n + 1):
            A[i] = data[idx]
            idx += 1

        if n <= SMALL:
            output.append(solve_small(n, adj, A))
        else:
            output.append(solve_large(n, adj, A))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()