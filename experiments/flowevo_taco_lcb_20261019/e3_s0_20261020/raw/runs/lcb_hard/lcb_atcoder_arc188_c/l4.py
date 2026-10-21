import sys

sys.setrecursionlimit(1 << 25)


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    N = next(it)
    M = next(it)

    V = 2 * N
    # Variables:
    # 0 .. N-1       : p_i = x_i XOR y_i
    # N .. 2N-1      : x_i, where x_i=0 honest, x_i=1 liar
    # y_i = confused flag = p_i XOR x_i

    parent = list(range(V))
    size = [1] * V
    parity = [0] * V  # value[x] XOR value[parent[x]]

    def find(x):
        if parent[x] == x:
            return x, 0
        p = parent[x]
        r, pp = find(p)
        parity[x] ^= pp
        parent[x] = r
        return parent[x], parity[x]

    def unite(x, y, w):
        # impose value[x] XOR value[y] = w
        rx, px = find(x)
        ry, py = find(y)

        if rx == ry:
            return (px ^ py) == w

        if size[rx] < size[ry]:
            parent[rx] = ry
            parity[rx] = px ^ py ^ w
            size[ry] += size[rx]
        else:
            parent[ry] = rx
            parity[ry] = px ^ py ^ w
            size[rx] += size[ry]
        return True

    for _ in range(M):
        a = next(it) - 1
        b = next(it) - 1
        c = next(it)

        # p_a XOR x_b = c
        if not unite(a, N + b, c):
            print(-1)
            return

    # Now find the lexicographically smallest valid confused-villager string.
    # Different connected components have independent root values.
    zparent = list(range(V))
    zsize = [1] * V
    zpar = [0] * V  # z_value[x] XOR z_value[zparent[x]]

    def zfind(x):
        if zparent[x] == x:
            return x, 0
        p = zparent[x]
        r, pp = zfind(p)
        zpar[x] ^= pp
        zparent[x] = r
        return zparent[x], zpar[x]

    def zunite(x, y, w):
        # impose z_value[x] XOR z_value[y] = w
        rx, px = zfind(x)
        ry, py = zfind(y)

        if rx == ry:
            return (px ^ py) == w

        if zsize[rx] < zsize[ry]:
            zparent[rx] = ry
            zpar[rx] = px ^ py ^ w
            zsize[ry] += zsize[rx]
        else:
            zparent[ry] = rx
            zpar[ry] = px ^ py ^ w
            zsize[rx] += zsize[ry]
        return True

    ans = ['0'] * N

    for i in range(N):
        rp, pp = find(i)
        rx, px = find(N + i)

        # y_i = p_i XOR x_i
        #     = (pp XOR px) XOR z_rp XOR z_rx
        base = pp ^ px

        if rp == rx:
            ans[i] = str(base)
        else:
            # Try to make y_i = 0:
            # z_rp XOR z_rx = base
            if zunite(rp, rx, base):
                ans[i] = '0'
            else:
                ans[i] = '1'

    print(''.join(ans))


if __name__ == "__main__":
    solve()