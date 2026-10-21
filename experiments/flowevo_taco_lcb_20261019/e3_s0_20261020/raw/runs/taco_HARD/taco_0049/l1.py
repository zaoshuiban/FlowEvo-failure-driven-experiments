import sys
from array import array


def main():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        n = next(it)
    except StopIteration:
        return
    m = next(it)

    edges = []
    for i in range(m):
        u = next(it) - 1
        v = next(it) - 1
        w = next(it)
        edges.append((w, u, v, i))
    del it

    edges.sort()

    parent = [-1] * n
    in_mst = bytearray(m)
    adj = [[] for _ in range(n)]

    mst_weight = 0
    cnt = 0

    def find(x):
        while parent[x] >= 0:
            if parent[parent[x]] >= 0:
                parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for w, u, v, eid in edges:
        ru = find(u)
        rv = find(v)

        if ru != rv:
            if parent[ru] > parent[rv]:
                ru, rv = rv, ru

            parent[ru] += parent[rv]
            parent[rv] = ru

            in_mst[eid] = 1
            mst_weight += w

            adj[u].append((v, w))
            adj[v].append((u, w))

            cnt += 1
            if cnt == n - 1:
                break

    del find, parent

    LOG = max(1, n.bit_length())

    up = [array('i', [0]) * n for _ in range(LOG)]
    mx = [array('i', [0]) * n for _ in range(LOG)]
    depth = array('i', [-1]) * n

    depth[0] = 0
    up0 = up[0]
    mx0 = mx[0]

    stack = [0]
    while stack:
        u = stack.pop()
        next_depth = depth[u] + 1

        for v, w in adj[u]:
            if depth[v] == -1:
                depth[v] = next_depth
                up0[v] = u
                mx0[v] = w
                stack.append(v)

    del adj, stack

    for k in range(1, LOG):
        prev = up[k - 1]
        cur = up[k]
        prev_mx = mx[k - 1]
        cur_mx = mx[k]

        for v in range(n):
            p = prev[v]
            cur[v] = prev[p]

            a = prev_mx[v]
            b = prev_mx[p]
            cur_mx[v] = a if a > b else b

    def max_on_path(a, b, depth=depth, up=up, mx=mx, LOG=LOG):
        res = 0

        if depth[a] < depth[b]:
            a, b = b, a

        diff = depth[a] - depth[b]
        bit = 0

        while diff:
            if diff & 1:
                val = mx[bit][a]
                if val > res:
                    res = val
                a = up[bit][a]

            diff >>= 1
            bit += 1

        if a == b:
            return res

        for k in range(LOG - 1, -1, -1):
            upk = up[k]
            if upk[a] != upk[b]:
                mxk = mx[k]

                val = mxk[a]
                if val > res:
                    res = val

                val = mxk[b]
                if val > res:
                    res = val

                a = upk[a]
                b = upk[b]

        val = mx[0][a]
        if val > res:
            res = val

        val = mx[0][b]
        if val > res:
            res = val

        return res

    ans = [0] * m

    for w, u, v, eid in edges:
        if in_mst[eid]:
            ans[eid] = mst_weight
        else:
            ans[eid] = mst_weight + w - max_on_path(u, v)

    sys.stdout.write('\n'.join(map(str, ans)))


if __name__ == "__main__":
    main()