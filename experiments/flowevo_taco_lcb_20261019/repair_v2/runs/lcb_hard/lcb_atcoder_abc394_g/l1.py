import sys
from array import array


def main():
    input = sys.stdin.buffer.readline

    H, W = map(int, input().split())
    N = H * W

    F = []
    for _ in range(H):
        F.extend(map(int, input().split()))

    Q = int(input())

    # Build a maximum spanning tree of the grid cells.
    # Edge weight between adjacent cells = min(height[u], height[v]).
    order = list(range(N))
    order.sort(key=F.__getitem__, reverse=True)

    parent = [-1] * N
    size = [1] * N

    head = array('i', [-1]) * N
    to = array('i')
    weight = array('i')
    nxt = array('i')

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def unite(a, b):
        ra = find(a)
        rb = find(b)
        if ra == rb:
            return False
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
        return True

    def add_edge(a, b, w):
        idx = len(to)
        to.append(b)
        weight.append(w)
        nxt.append(head[a])
        head[a] = idx

        idx = len(to)
        to.append(a)
        weight.append(w)
        nxt.append(head[b])
        head[b] = idx

    for u in order:
        parent[u] = u
        size[u] = 1
        h = F[u]

        i = u // W
        j = u - i * W

        if i > 0:
            v = u - W
            if parent[v] != -1 and unite(u, v):
                add_edge(u, v, h)

        if i + 1 < H:
            v = u + W
            if parent[v] != -1 and unite(u, v):
                add_edge(u, v, h)

        if j > 0:
            v = u - 1
            if parent[v] != -1 and unite(u, v):
                add_edge(u, v, h)

        if j + 1 < W:
            v = u + 1
            if parent[v] != -1 and unite(u, v):
                add_edge(u, v, h)

    del order, parent, size

    INF = 10**9

    up0 = array('i', [-1]) * N
    depth = array('i', [0]) * N
    min0 = array('i', [INF]) * N

    up0[0] = 0
    stack = [0]

    while stack:
        u = stack.pop()
        e = head[u]
        pu = up0[u]
        nd = depth[u] + 1

        while e != -1:
            v = to[e]
            if v != pu:
                up0[v] = u
                depth[v] = nd
                min0[v] = weight[e]
                stack.append(v)
            e = nxt[e]

    LOG = N.bit_length()

    up = [up0]
    minw = [min0]

    for _ in range(1, LOG):
        prev = up[-1]
        prev_min = minw[-1]

        cur = array('i', [0]) * N
        cur_min = array('i', [INF]) * N

        for v in range(N):
            mid = prev[v]
            cur[v] = prev[mid]

            a = prev_min[v]
            b = prev_min[mid]
            cur_min[v] = a if a < b else b

        up.append(cur)
        minw.append(cur_min)

    out = []
    rev_range = range(LOG - 1, -1, -1)

    for _ in range(Q):
        A, B, Y, C, D, Z = map(int, input().split())

        s = (A - 1) * W + (B - 1)
        t = (C - 1) * W + (D - 1)

        if s == t:
            bottleneck = F[s]
        else:
            u = s
            v = t
            res = INF

            if depth[u] < depth[v]:
                u, v = v, u

            diff = depth[u] - depth[v]
            bit = 0

            while diff:
                if diff & 1:
                    val = minw[bit][u]
                    if val < res:
                        res = val
                    u = up[bit][u]
                diff >>= 1
                bit += 1

            if u != v:
                for k in rev_range:
                    uu = up[k][u]
                    vv = up[k][v]

                    if uu != vv:
                        val = minw[k][u]
                        if val < res:
                            res = val

                        val = minw[k][v]
                        if val < res:
                            res = val

                        u = uu
                        v = vv

                val = minw[0][u]
                if val < res:
                    res = val

                val = minw[0][v]
                if val < res:
                    res = val

            bottleneck = res

        if Y < Z:
            low = Y
            floor_diff = Z - Y
        else:
            low = Z
            floor_diff = Y - Z

        if low > bottleneck:
            ans = floor_diff + 2 * (low - bottleneck)
        else:
            ans = floor_diff

        out.append(str(ans))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()