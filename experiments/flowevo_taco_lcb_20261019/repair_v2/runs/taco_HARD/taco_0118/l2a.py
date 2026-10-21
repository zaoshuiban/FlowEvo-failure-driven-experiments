import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    a = [0] + data[1:n + 1]
    pos = n + 1

    adj = [[] for _ in range(n + 1)]
    for _ in range(n - 1):
        u = data[pos]
        v = data[pos + 1]
        pos += 2
        adj[u].append(v)
        adj[v].append(u)

    del data

    max_a = max(a)
    EMPTY = ()

    if max_a >= 2:
        spf = list(range(max_a + 1))
        spf[1] = 1

        i = 2
        while i * i <= max_a:
            if spf[i] == i:
                for j in range(i * i, max_a + 1, i):
                    if spf[j] == j:
                        spf[j] = i
            i += 1

        factors = [None] * (n + 1)

        for v in range(1, n + 1):
            x = a[v]
            fs = []

            while x > 1:
                p = spf[x]
                fs.append(p)
                while x % p == 0:
                    x //= p

            factors[v] = fs if fs else EMPTY
    else:
        factors = [EMPTY] * (n + 1)

    del a

    parent = [0] * (n + 1)
    parent[1] = -1
    order = [1]

    idx = 0
    while idx < len(order):
        v = order[idx]
        idx += 1

        for u in adj[v]:
            if u != parent[v]:
                parent[u] = v
                order.append(u)

    dp = [None] * (n + 1)
    answer = 0

    for v in reversed(order):
        fv = factors[v]
        m = len(fv)

        if m == 0:
            dp[v] = EMPTY
            continue

        top1 = [0] * m
        top2 = [0] * m
        pv = parent[v]

        for u in adj[v]:
            if u == pv:
                continue

            fu = factors[u]
            if not fu:
                continue

            dpu = dp[u]
            i = 0
            j = 0
            lfu = len(fu)

            while i < m and j < lfu:
                if fv[i] == fu[j]:
                    value = dpu[j]

                    if value > top1[i]:
                        top2[i] = top1[i]
                        top1[i] = value
                    elif value > top2[i]:
                        top2[i] = value

                    i += 1
                    j += 1
                elif fv[i] < fu[j]:
                    i += 1
                else:
                    j += 1

        current_dp = [0] * m

        for i in range(m):
            value = top1[i] + 1
            current_dp[i] = value

            candidate = value + top2[i]
            if candidate > answer:
                answer = candidate

        dp[v] = current_dp

    print(answer)


if __name__ == "__main__":
    main()