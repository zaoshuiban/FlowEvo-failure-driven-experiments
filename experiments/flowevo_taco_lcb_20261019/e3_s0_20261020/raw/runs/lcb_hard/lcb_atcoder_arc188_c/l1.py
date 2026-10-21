import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N, M = data[0], data[1]
    V = 2 * N

    parent = list(range(V))
    size = [1] * V
    diff = [0] * V  # diff[x] = value[x] XOR value[parent[x]]

    def find(x):
        if parent[x] == x:
            return x, 0

        root = x
        parity = 0
        while parent[root] != root:
            parity ^= diff[root]
            root = parent[root]

        cur = x
        acc = 0
        while parent[cur] != cur:
            nxt = parent[cur]
            old = diff[cur]
            diff[cur] = acc ^ parity
            parent[cur] = root
            acc ^= old
            cur = nxt

        return root, parity

    ok = True
    idx = 2

    for _ in range(M):
        a = data[idx] - 1
        b = data[idx + 1] - 1
        c = data[idx + 2]
        idx += 3

        u = a          # P_a = honest/liar_A XOR confused_A
        v = N + b      # Q_b = honest/liar_B

        ru, pu = find(u)
        rv, pv = find(v)

        if ru == rv:
            if (pu ^ pv) != c:
                ok = False
        else:
            d = pu ^ pv ^ c

            if size[ru] < size[rv]:
                parent[ru] = rv
                diff[ru] = d
                size[rv] += size[ru]
            else:
                parent[rv] = ru
                diff[rv] = d
                size[ru] += size[rv]

    if not ok:
        print(-1)
        return

    value = [0] * V
    for i in range(V):
        _, value[i] = find(i)

    ans = []
    for i in range(N):
        confused = value[i] ^ value[N + i]
        ans.append('1' if confused else '0')

    print(''.join(ans))


if __name__ == "__main__":
    solve()