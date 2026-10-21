import sys


def process_case(n, adj, A):
    # Root the tree at node 0 and get a DFS preorder.
    parent = [-1] * n
    tin = [0] * n
    order = []

    parent[0] = -2
    stack = [0]

    while stack:
        u = stack.pop()
        tin[u] = len(order)
        order.append(u)

        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                stack.append(v)

    # Subtree sizes and heavy child.
    size = [1] * n
    heavy = [-1] * n

    for u in reversed(order):
        total = 1
        best = -1
        best_sz = 0

        for v in adj[u]:
            if parent[v] == u:
                sv = size[v]
                total += sv
                if sv > best_sz:
                    best_sz = sv
                    best = v

        size[u] = total
        heavy[u] = best

    # Coordinate compression of values.
    values = sorted(set(A))
    m = len(values)
    rank = {v: i for i, v in enumerate(values)}
    ranks = [rank[x] for x in A]

    base = 1
    while base < m:
        base <<= 1

    total_len = base << 1
    INF = 1 << 60

    # Segment tree over values sorted by rank.
    # It stores first active value, last active value and minimum XOR
    # between adjacent active distinct values inside the segment.
    first = [-1] * total_len
    last = [-1] * total_len
    mn = [INF] * total_len

    cnt = [0] * m
    dup = 0  # number of distinct values whose frequency is at least 2

    def insert_rank(r):
        nonlocal dup

        c = cnt[r]

        if c == 0:
            p = base + r
            v = values[r]
            first[p] = v
            last[p] = v
            mn[p] = INF
            p >>= 1

            while p:
                lc = p << 1
                rc = lc | 1

                if first[lc] == -1:
                    first[p] = first[rc]
                    last[p] = last[rc]
                    mn[p] = mn[rc]
                elif first[rc] == -1:
                    first[p] = first[lc]
                    last[p] = last[lc]
                    mn[p] = mn[lc]
                else:
                    first[p] = first[lc]
                    last[p] = last[rc]

                    cross = last[lc] ^ first[rc]
                    best = mn[lc] if mn[lc] < mn[rc] else mn[rc]
                    if cross < best:
                        best = cross
                    mn[p] = best

                p >>= 1

        c += 1
        cnt[r] = c

        if c == 2:
            dup += 1

    def delete_rank(r):
        nonlocal dup

        c = cnt[r]

        if c == 2:
            dup -= 1

        c -= 1
        cnt[r] = c

        if c == 0:
            p = base + r
            first[p] = -1
            last[p] = -1
            mn[p] = INF
            p >>= 1

            while p:
                lc = p << 1
                rc = lc | 1

                if first[lc] == -1:
                    first[p] = first[rc]
                    last[p] = last[rc]
                    mn[p] = mn[rc]
                elif first[rc] == -1:
                    first[p] = first[lc]
                    last[p] = last[lc]
                    mn[p] = mn[lc]
                else:
                    first[p] = first[lc]
                    last[p] = last[rc]

                    cross = last[lc] ^ first[rc]
                    best = mn[lc] if mn[lc] < mn[rc] else mn[rc]
                    if cross < best:
                        best = cross
                    mn[p] = best

                p >>= 1

    ans = [-1] * n

    # Iterative DSU on tree.
    # Frame: (u, keep, state, next_index)
    dsu_stack = [(0, 0, 0, 0)]

    while dsu_stack:
        u, keep, state, idx = dsu_stack[-1]

        if state == 0:
            adju = adj[u]

            while idx < len(adju):
                v = adju[idx]
                if parent[v] == u and v != heavy[u]:
                    break
                idx += 1

            if idx < len(adju):
                v = adju[idx]
                dsu_stack[-1] = (u, keep, 0, idx + 1)
                dsu_stack.append((v, 0, 0, 0))
            else:
                dsu_stack[-1] = (u, keep, 1, 0)

        elif state == 1:
            h = heavy[u]

            if h != -1:
                dsu_stack[-1] = (u, keep, 2, 0)
                dsu_stack.append((h, 1, 0, 0))
            else:
                dsu_stack[-1] = (u, keep, 2, 0)

        elif state == 2:
            # Add all light subtrees.
            for v in adj[u]:
                if parent[v] == u and v != heavy[u]:
                    l = tin[v]
                    r = l + size[v]

                    for p in range(l, r):
                        node = order[p]
                        insert_rank(ranks[node])

            # Add u itself.
            insert_rank(ranks[u])

            if size[u] >= 2:
                if dup > 0:
                    ans[u] = 0
                else:
                    ans[u] = mn[1]
            else:
                ans[u] = -1

            dsu_stack[-1] = (u, keep, 3, 0)

        else:
            if keep == 0:
                l = tin[u]
                r = l + size[u]

                for p in range(l, r):
                    node = order[p]
                    delete_rank(ranks[node])

            dsu_stack.pop()

    return ans


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(data)

    output = []

    for _ in range(t):
        n = next(data)

        adj = [[] for _ in range(n)]

        for _ in range(n - 1):
            u = next(data) - 1
            v = next(data) - 1
            adj[u].append(v)
            adj[v].append(u)

        A = [next(data) for _ in range(n)]

        if n == 1:
            output.append("-1")
            continue

        ans = process_case(n, adj, A)
        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()