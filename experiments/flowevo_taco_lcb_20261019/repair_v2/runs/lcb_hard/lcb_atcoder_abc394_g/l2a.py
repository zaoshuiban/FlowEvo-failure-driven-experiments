import sys
from array import array


def int_stream():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False
    for c in data:
        if c >= 48:
            num = num * 10 + (c - 48)
            in_num = True
        elif in_num:
            yield num
            num = 0
            in_num = False
    if in_num:
        yield num


def main():
    it = int_stream()

    H = next(it)
    W = next(it)
    N = H * W

    F = [0] * N
    for i in range(N):
        F[i] = next(it)

    # Build all adjacency edges of the grid.
    # Edge weight between adjacent cells is min(height[u], height[v]).
    edges = []
    append = edges.append

    for i in range(H):
        base = i * W
        for j in range(W):
            u = base + j
            fu = F[u]

            if i + 1 < H:
                v = u + W
                fv = F[v]
                w = fu if fu < fv else fv
                append((w, u, v))

            if j + 1 < W:
                v = u + 1
                fv = F[v]
                w = fu if fu < fv else fv
                append((w, u, v))

    edges.sort(reverse=True)
    del F

    parent = list(range(N))
    size = [1] * N
    graph = [[] for _ in range(N)]

    edge_count = 0

    # Kruskal for maximum spanning tree.
    for w, u, v in edges:
        ru = u
        while parent[ru] != ru:
            parent[ru] = parent[parent[ru]]
            ru = parent[ru]

        rv = v
        while parent[rv] != rv:
            parent[rv] = parent[parent[rv]]
            rv = parent[rv]

        if ru == rv:
            continue

        if size[ru] < size[rv]:
            ru, rv = rv, ru

        parent[rv] = ru
        size[ru] += size[rv]

        graph[u].append((v, w))
        graph[v].append((u, w))

        edge_count += 1
        if edge_count == N - 1:
            break

    del edges, parent, size

    INF = 10**9

    depth = array('I', [0]) * N
    up0 = array('I', [0]) * N
    mn0 = array('I', [INF]) * N

    up0[0] = 0
    mn0[0] = INF

    # Iterative DFS on the maximum spanning tree.
    stack = [0]
    while stack:
        u = stack.pop()
        next_depth = depth[u] + 1
        parent_u = up0[u]

        for v, w in graph[u]:
            if v == parent_u:
                continue

            depth[v] = next_depth
            up0[v] = u
            mn0[v] = w
            stack.append(v)

    del graph

    LOG = N.bit_length()
    up = [up0]
    mn = [mn0]

    for _ in range(1, LOG):
        prev_up = up[-1]
        prev_mn = mn[-1]

        cur_up = array('I', [0]) * N
        cur_mn = array('I', [INF]) * N

        for v in range(N):
            mid = prev_up[v]
            cur_up[v] = prev_up[mid]

            a = prev_mn[v]
            b = prev_mn[mid]
            cur_mn[v] = a if a < b else b

        up.append(cur_up)
        mn.append(cur_mn)

    Q = next(it)
    answers = []

    for _ in range(Q):
        A = next(it) - 1
        B = next(it) - 1
        Y = next(it)

        C = next(it) - 1
        D = next(it) - 1
        Z = next(it)

        u = A * W + B
        v = C * W + D

        if u == v:
            ans = Y - Z if Y >= Z else Z - Y
            answers.append(str(ans))
            continue

        limit = Y if Y < Z else Z

        # LCA with minimum edge weight on the path in the maximum spanning tree.
        uu = u
        vv = v

        if depth[uu] < depth[vv]:
            uu, vv = vv, uu

        bottleneck = INF

        diff = depth[uu] - depth[vv]
        bit = 0

        while diff:
            if diff & 1:
                val = mn[bit][uu]
                if val < bottleneck:
                    bottleneck = val
                uu = up[bit][uu]

            diff >>= 1
            bit += 1

        if uu != vv:
            for k in range(LOG - 1, -1, -1):
                au = up[k][uu]
                av = up[k][vv]

                if au != av:
                    val = mn[k][uu]
                    if val < bottleneck:
                        bottleneck = val

                    val = mn[k][vv]
                    if val < bottleneck:
                        bottleneck = val

                    uu = au
                    vv = av

            val = mn[0][uu]
            if val < bottleneck:
                bottleneck = val

            val = mn[0][vv]
            if val < bottleneck:
                bottleneck = val

        best_floor = limit if limit < bottleneck else bottleneck
        ans = Y + Z - 2 * best_floor

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()