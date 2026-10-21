import sys

MOD = 998244353


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
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

        total = n - 1

        # Root the tree at 0.
        parent = [-1] * n
        order = [0]
        parent[0] = -1

        it = 0
        while it < len(order):
            v = order[it]
            it += 1
            for to in adj[v]:
                if to != parent[v]:
                    parent[to] = v
                    order.append(to)

        rev_order = order[::-1]
        max_degree = max(len(x) for x in adj)

        # All possible gcds divide total = n - 1.
        divisors = []
        d = 1
        while d * d <= total:
            if total % d == 0:
                divisors.append(d)
                q = total // d
                if q != d:
                    divisors.append(q)
            d += 1
        divisors.sort(reverse=True)

        # F[k] = number of orientations with all outdegrees divisible by k.
        # For k > 1, there is at most one such orientation.
        F = {1: pow(2, total, MOD)}

        for k in divisors:
            if k == 1:
                continue

            if k > max_degree:
                F[k] = 0
                continue

            cnt = [0] * n
            ok = True

            for v in rev_order:
                r = cnt[v] % k

                if v == 0:
                    if r != 0:
                        ok = False
                        break
                else:
                    if r == 0:
                        # Edge v -> parent is not used; parent -> v contributes.
                        cnt[parent[v]] += 1
                    elif r == k - 1:
                        # Edge v -> parent is used.
                        pass
                    else:
                        ok = False
                        break

            F[k] = 1 if ok else 0

        # Möbius inversion over divisors:
        # F[k] = sum_{m multiple of k} A[m]
        ans = {}
        for d in divisors:
            val = F[d]
            for m in divisors:
                if m > d and m % d == 0:
                    val -= ans[m]
            ans[d] = val % MOD

        result = []
        for k in range(1, n + 1):
            if total % k == 0:
                result.append(str(ans.get(k, 0)))
            else:
                result.append("0")

        outputs.append(" ".join(result))

    sys.stdout.write("\n".join(outputs))


if __name__ == "__main__":
    solve()