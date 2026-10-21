import sys

MOD = 998244353
MAXM = 300005


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    # Möbius function up to MAXM
    mu = [0] * (MAXM + 1)
    mu[1] = 1
    primes = []
    composite = bytearray(MAXM + 1)

    for i in range(2, MAXM + 1):
        if not composite[i]:
            primes.append(i)
            mu[i] = -1

        for p in primes:
            v = i * p
            if v > MAXM:
                break
            composite[v] = 1
            if i % p == 0:
                mu[v] = 0
                break
            else:
                mu[v] = -mu[i]

    pow2 = [1] * (MAXM + 1)
    for i in range(1, MAXM + 1):
        pow2[i] = (pow2[i - 1] * 2) % MOD

    ptr = 0
    t = data[ptr]
    ptr += 1

    answers = []

    for _ in range(t):
        n = data[ptr]
        ptr += 1

        adj = [[] for _ in range(n)]

        for _ in range(n - 1):
            u = data[ptr] - 1
            v = data[ptr + 1] - 1
            ptr += 2
            adj[u].append(v)
            adj[v].append(u)

        parent = [-1] * n
        parent[0] = -2
        order = [0]

        for v in order:
            pv = parent[v]
            for to in adj[v]:
                if to != pv:
                    parent[to] = v
                    order.append(to)

        postorder = order[::-1]

        f = [0] * (n + 1)
        f[1] = pow2[n - 1]

        total = n - 1
        par = parent
        po = postorder

        for d in range(2, n):
            if total % d != 0:
                continue

            cnt = [0] * n
            ok = True

            for v in po:
                x = cnt[v] % d
                p = par[v]

                if p == -2:
                    if x != 0:
                        ok = False
                        break
                else:
                    if x == 0:
                        cnt[p] += 1
                    elif x == d - 1:
                        pass
                    else:
                        ok = False
                        break

            if ok:
                f[d] = 1

        ans = [0] * (n + 1)

        for k in range(1, n + 1):
            s = 0
            d = k
            m = 1

            while d <= n:
                if f[d]:
                    mm = mu[m]
                    if mm:
                        s += mm * f[d]
                d += k
                m += 1

            ans[k] = s % MOD

        answers.append(' '.join(str(ans[k]) for k in range(1, n + 1)))

    sys.stdout.write('\n'.join(answers))


if __name__ == "__main__":
    solve()