import sys
from math import gcd
from collections import defaultdict


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]

    a = [0] * (n + 1)
    for i in range(1, n + 1):
        a[i] = data[i]

    max_a = max(a)
    has_greater_than_one = max_a > 1

    # Smallest prime factor sieve
    spf = list(range(max_a + 1))
    if max_a >= 1:
        spf[1] = 1

    limit = int(max_a ** 0.5)
    for i in range(2, limit + 1):
        if spf[i] == i:
            for j in range(i * i, max_a + 1, i):
                if spf[j] == j:
                    spf[j] = i

    shift = n.bit_length()
    mask = (1 << shift) - 1

    edges_by_prime = defaultdict(list)

    idx = n + 1
    for _ in range(n - 1):
        u = data[idx]
        v = data[idx + 1]
        idx += 2

        g = gcd(a[u], a[v])
        if g > 1:
            code = (u << shift) | v
            while g > 1:
                p = spf[g]
                edges_by_prime[p].append(code)
                while g % p == 0:
                    g //= p

    answer = 1 if has_greater_than_one else 0

    seen = [0] * (n + 1)

    for p, edges in edges_by_prime.items():
        if len(edges) == 1:
            if answer < 2:
                answer = 2
            continue

        if answer == n:
            break

        adj = {}

        for code in edges:
            u = code >> shift
            v = code & mask

            lst = adj.get(u)
            if lst is None:
                adj[u] = [v]
            else:
                lst.append(v)

            lst = adj.get(v)
            if lst is None:
                adj[v] = [u]
            else:
                lst.append(u)

        for start in adj:
            if seen[start] == p:
                continue

            # First DFS: find one endpoint of a diameter
            stack = [(start, 0)]
            seen[start] = p

            far_node = start
            max_dist = 0

            while stack:
                u, dist = stack.pop()

                if dist > max_dist:
                    max_dist = dist
                    far_node = u

                for v in adj[u]:
                    if seen[v] != p:
                        seen[v] = p
                        stack.append((v, dist + 1))

            # Second DFS: find diameter length in edges
            stack = [(far_node, -1, 0)]
            diameter_edges = 0

            while stack:
                u, parent, dist = stack.pop()

                if dist > diameter_edges:
                    diameter_edges = dist

                for v in adj[u]:
                    if v != parent:
                        stack.append((v, u, dist + 1))

            candidate = diameter_edges + 1
            if candidate > answer:
                answer = candidate

            if answer == n:
                break

        if answer == n:
            break

    print(answer)


if __name__ == "__main__":
    main()