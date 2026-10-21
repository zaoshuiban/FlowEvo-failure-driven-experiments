import sys

MOD = 998244353


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    outputs = []

    for _ in range(t):
        n = data[pos]
        pos += 1

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            u = data[pos] - 1
            v = data[pos + 1] - 1
            pos += 2
            adj[u].append(v)
            adj[v].append(u)

        parent = [-1] * n
        parent[0] = 0
        children = [[] for _ in range(n)]
        order = [0]

        for v in order:
            for to in adj[v]:
                if to == parent[v]:
                    continue
                parent[to] = v
                children[v].append(to)
                order.append(to)

        rev_order = order[::-1]
        x = [0] * n

        def possible(g: int) -> bool:
            for v in rev_order:
                cnt = 0
                for c in children[v]:
                    if x[c] == 0:
                        cnt += 1

                if v == 0:
                    if cnt % g != 0:
                        return False
                else:
                    r = cnt % g
                    if r == 0:
                        x[v] = 0
                    elif r == g - 1:
                        x[v] = 1
                    else:
                        return False

            return True

        m = n - 1

        divisors = []
        d = 1
        while d * d <= m:
            if m % d == 0:
                divisors.append(d)
                if d * d != m:
                    divisors.append(m // d)
            d += 1
        divisors.sort()

        f = {}
        f[1] = pow(2, m, MOD)

        for d in divisors:
            if d > 1:
                f[d] = 1 if possible(d) else 0

        ans = {}
        for d in reversed(divisors):
            val = f[d]
            for e in divisors:
                if e > d and e % d == 0:
                    val -= ans[e]
            ans[d] = val % MOD

        result = [0] * n
        for d, val in ans.items():
            if d <= n:
                result[d - 1] = val

        outputs.append(" ".join(map(str, result)))

    sys.stdout.write("\n".join(outputs))


if __name__ == "__main__":
    solve()