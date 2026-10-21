import sys
from math import gcd


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    a = [0] * (n + 1)
    max_a = 0

    for i in range(1, n + 1):
        x = data[idx]
        idx += 1
        a[i] = x
        if x > max_a:
            max_a = x

    edges_by_gcd = [[] for _ in range(max_a + 1)]

    for _ in range(n - 1):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        g = gcd(a[u], a[v])
        edges_by_gcd[g].append((u, v))

    pos = [[] for _ in range(max_a + 1)]
    for i in range(1, n + 1):
        pos[a[i]].append(i)

    del data

    # F[d] will first store the number of pairs whose path gcd is divisible by d.
    F = [0] * (max_a + 1)

    # All pairs have path gcd divisible by 1.
    F[1] = n * (n + 1) // 2

    parent = [0] * (n + 1)
    size = [0] * (n + 1)

    limit = max_a + 1

    for d in range(2, limit):
        total = 0

        # Activate all vertices whose value is divisible by d.
        for val in range(d, limit, d):
            for v in pos[val]:
                parent[v] = v
                size[v] = 1
                total += 1

        if total == 0:
            continue

        # Process all active edges: d divides gcd(a[u], a[v]).
        for g in range(d, limit, d):
            for u, v in edges_by_gcd[g]:
                ru = u
                while parent[ru] != ru:
                    parent[ru] = parent[parent[ru]]
                    ru = parent[ru]

                rv = v
                while parent[rv] != rv:
                    parent[rv] = parent[parent[rv]]
                    rv = parent[rv]

                # Active edges form a forest, so ru != rv.
                if size[ru] < size[rv]:
                    ru, rv = rv, ru

                total += size[ru] * size[rv]
                parent[rv] = ru
                size[ru] += size[rv]

        F[d] = total

    # Mobius-like inversion over multiples:
    # exact[d] = F[d] - sum(exact[multiple of d]).
    for d in range(max_a, 0, -1):
        value = F[d]
        if value == 0:
            continue

        for multiple in range(d + d, limit, d):
            value -= F[multiple]

        F[d] = value

    out = []
    for i in range(1, limit):
        if F[i] > 0:
            out.append(f"{i} {F[i]}")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()