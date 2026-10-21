import sys
from math import gcd

MOD = 998244353


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    outputs = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            u = data[idx] - 1
            v = data[idx + 1] - 1
            idx += 2
            adj[u].append(v)
            adj[v].append(u)

        # Only prime divisors of n - 1 are needed.
        y = n - 1
        factors = []

        if y % 2 == 0:
            factors.append(2)
            while y % 2 == 0:
                y //= 2

        p = 3
        while p * p <= y:
            if y % p == 0:
                factors.append(p)
                while y % p == 0:
                    y //= p
            p += 2

        if y > 1:
            factors.append(y)

        if not factors:
            ans = [0] * (n + 1)
            ans[1] = pow(2, n - 1, MOD)
            outputs.append(" ".join(str(ans[i]) for i in range(1, n + 1)))
            continue

        parent = [-1] * n
        parent[0] = -2
        order = [0]

        for v in order:
            pv = parent[v]
            for u in adj[v]:
                if u != pv:
                    parent[u] = v
                    order.append(u)

        rev_order = order[::-1]
        exact_gcds = set()

        for k in factors:
            out_child = [0] * n
            g = 0
            ok = True

            for v in rev_order:
                cur_out = out_child[v]
                rem = cur_out % k

                if v == 0:
                    if rem != 0:
                        ok = False
                        break
                    degree = cur_out
                else:
                    if rem == 0:
                        x = 0
                    elif rem == k - 1:
                        x = 1
                    else:
                        ok = False
                        break

                    degree = cur_out + x

                    if x == 0:
                        out_child[parent[v]] += 1

                if degree:
                    if g == 0:
                        g = degree
                    elif g != k:
                        g = gcd(g, degree)

            if ok:
                exact_gcds.add(g)

        ans = [0] * (n + 1)
        ans[1] = (pow(2, n - 1, MOD) - len(exact_gcds)) % MOD

        for g in exact_gcds:
            ans[g] = 1

        outputs.append(" ".join(str(ans[i]) for i in range(1, n + 1)))

    sys.stdout.write("\n".join(outputs))


if __name__ == "__main__":
    solve()