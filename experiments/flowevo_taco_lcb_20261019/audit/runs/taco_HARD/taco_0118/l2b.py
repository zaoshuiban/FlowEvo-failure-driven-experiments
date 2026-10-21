import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [0] + data[1:n + 1]

    max_a = max(a)
    if max_a <= 1:
        print(0)
        return

    adj = [[] for _ in range(n + 1)]
    pos = n + 1
    for _ in range(n - 1):
        x = data[pos]
        y = data[pos + 1]
        pos += 2
        adj[x].append(y)
        adj[y].append(x)

    del data

    # Smallest prime factor sieve
    spf = list(range(max_a + 1))
    for i in range(2, int(max_a ** 0.5) + 1):
        if spf[i] == i:
            for j in range(i * i, max_a + 1, i):
                if spf[j] == j:
                    spf[j] = i

    # Distinct prime factors of each vertex value
    factors = [None] * (n + 1)
    for i in range(1, n + 1):
        x = a[i]
        cur = []
        while x > 1:
            p = spf[x]
            cur.append(p)
            while x % p == 0:
                x //= p
        factors[i] = cur

    del spf

    # Root the tree at vertex 1
    parent = [0] * (n + 1)
    order = [1]
    idx = 0

    while idx < len(order):
        v = order[idx]
        idx += 1
        for u in adj[v]:
            if u == parent[v]:
                continue
            parent[u] = v
            order.append(u)

    dp = [None] * (n + 1)
    answer = 0

    for v in reversed(order):
        fv = factors[v]
        m = len(fv)

        if m == 0:
            dp[v] = None
            continue

        best1 = [0] * m
        best2 = [0] * m
        av = a[v]
        pv = parent[v]

        for u in adj[v]:
            if u == pv:
                continue

            fu = factors[u]
            if not fu:
                continue

            du = dp[u]

            for j, p in enumerate(fu):
                if av % p == 0:
                    for k in range(m):
                        if fv[k] == p:
                            break

                    val = du[j]

                    if val > best1[k]:
                        best2[k] = best1[k]
                        best1[k] = val
                    elif val > best2[k]:
                        best2[k] = val

        dv = [0] * m

        for k in range(m):
            dv[k] = best1[k] + 1
            candidate = best1[k] + best2[k] + 1
            if candidate > answer:
                answer = candidate

        dp[v] = dv

    print(answer)


if __name__ == "__main__":
    main()