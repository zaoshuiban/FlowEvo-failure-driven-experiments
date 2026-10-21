import sys


def solve():
    input = sys.stdin.buffer.readline
    H, W, N = map(int, input().split())

    R = [0] * N
    C = [0] * N
    L = [0] * N

    for i in range(N):
        r, c, l = map(int, input().split())
        R[i] = r
        C[i] = c - 1
        L[i] = l

    order = list(range(N))
    order.sort(key=lambda i: R[i], reverse=True)

    INF = 10**18
    tree = [INF] * (4 * W + 5)
    lazy = [-1] * (4 * W + 5)

    def assign(node, left, right, ql, qr, val):
        if ql <= left and right <= qr:
            tree[node] = val
            lazy[node] = val
            return

        lc = node * 2
        rc = lc + 1

        if lazy[node] != -1:
            v = lazy[node]
            tree[lc] = tree[rc] = v
            lazy[lc] = lazy[rc] = v
            lazy[node] = -1

        mid = (left + right) // 2
        if ql <= mid:
            assign(lc, left, mid, ql, qr, val)
        if mid < qr:
            assign(rc, mid + 1, right, ql, qr, val)

        tree[node] = min(tree[lc], tree[rc])

    def query(node, left, right, ql, qr):
        if ql <= left and right <= qr:
            return tree[node]

        lc = node * 2
        rc = lc + 1

        if lazy[node] != -1:
            v = lazy[node]
            tree[lc] = tree[rc] = v
            lazy[lc] = lazy[rc] = v
            lazy[node] = -1

        mid = (left + right) // 2
        res = INF

        if ql <= mid:
            res = query(lc, left, mid, ql, qr)
        if mid < qr:
            res = min(res, query(rc, mid + 1, right, ql, qr))

        return res

    ans = [0] * N

    for i in order:
        ql = C[i]
        qr = C[i] + L[i] - 1

        mn = query(1, 0, W - 1, ql, qr)

        if mn == INF:
            final_row = H
        else:
            final_row = mn - 1

        ans[i] = final_row
        assign(1, 0, W - 1, ql, qr, final_row)

    sys.stdout.write("\n".join(map(str, ans)))


if __name__ == "__main__":
    solve()