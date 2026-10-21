import sys
from array import array


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    U = [0] * m
    V = [0] * m
    W = [0] * m

    pos = 2
    for i in range(m):
        U[i] = data[pos] - 1
        V[i] = data[pos + 1] - 1
        W[i] = data[pos + 2]
        pos += 3

    del data

    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    order = list(range(m))
    order.sort(key=W.__getitem__)

    mst_adj = [[] for _ in range(n)]
    mst_weight = 0

    for idx in order:
        u = U[idx]
        v = V[idx]
        ru = find(u)
        rv = find(v)

        if ru != rv:
            if size[ru] < size[rv]:
                ru, rv = rv, ru

            parent[rv] = ru
            size[ru] += size[rv]

            w = W[idx]
            mst_weight += w
            mst_adj[u].append((v, w))
            mst_adj[v].append((u, w))

    del parent, size, order

    LOG = max(1, n.bit_length())

    up = [array('i', [-1]) * n for _ in range(LOG)]
    mx = [array('i', [0]) * n for _ in range(LOG)]
    depth = array('i', [0]) * n

    up0 = up[0]
    mx0 = mx[0]
    up0[0] = 0

    stack = [0]
    while stack:
        v = stack.pop()

        for to, w in mst_adj[v]:
            if up0[to] == -1:
                up0[to] = v
                mx0[to] = w
                depth[to] = depth[v] + 1
                stack.append(to)

    del mst_adj, stack

    for k in range(1, LOG):
        prev_up = up[k - 1]
        cur_up = up[k]
        prev_mx = mx[k - 1]
        cur_mx = mx[k]

        for v in range(n):
            a = prev_up[v]
            cur_up[v] = prev_up[a]

            m1 = prev_mx[v]
            m2 = prev_mx[a]
            cur_mx[v] = m1 if m1 > m2 else m2

    def path_max(u, v):
        ans = 0

        if depth[u] < depth[v]:
            u, v = v, u

        diff = depth[u] - depth[v]
        bit = 0

        while diff:
            if diff & 1:
                val = mx[bit][u]
                if val > ans:
                    ans = val
                u = up[bit][u]

            diff >>= 1
            bit += 1

        if u == v:
            return ans

        for k in range(LOG - 1, -1, -1):
            uu = up[k][u]
            vv = up[k][v]

            if uu != vv:
                val = mx[k][u]
                if val > ans:
                    ans = val

                val = mx[k][v]
                if val > ans:
                    ans = val

                u = uu
                v = vv

        val = mx[0][u]
        if val > ans:
            ans = val

        val = mx[0][v]
        if val > ans:
            ans = val

        return ans

    out = []
    append = out.append

    for i in range(m):
        answer = mst_weight + W[i] - path_max(U[i], V[i])
        append(str(answer))

    sys.stdout.write('\n'.join(out))
    if out:
        sys.stdout.write('\n')


if __name__ == "__main__":
    main()