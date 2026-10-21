import sys
from math import isqrt


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
    idx = n + 1
    for _ in range(n - 1):
        x = data[idx]
        y = data[idx + 1]
        idx += 2
        adj[x].append(y)
        adj[y].append(x)

    del data

    # Smallest prime factor sieve
    spf = list(range(max_a + 1))
    limit = isqrt(max_a)
    for i in range(2, limit + 1):
        if spf[i] == i:
            for j in range(i * i, max_a + 1, i):
                if spf[j] == j:
                    spf[j] = i

    # For every prime, store vertices whose value is divisible by it
    by_prime = {}
    for v in range(1, n + 1):
        x = a[v]
        while x > 1:
            p = spf[x]
            if p in by_prime:
                by_prime[p].append(v)
            else:
                by_prime[p] = [v]

            while x % p == 0:
                x //= p

    visited = [0] * (n + 1)
    stamp = 0
    answer = 0

    for p, vertices in by_prime.items():
        stamp += 1

        for start in vertices:
            if visited[start] == stamp:
                continue

            # First DFS: collect one component and find one diameter endpoint
            far_node = start
            far_dist = -1
            size = 0
            stack = [(start, 0, 0)]

            while stack:
                v, parent, dist = stack.pop()
                visited[v] = stamp
                size += 1

                if dist > far_dist:
                    far_dist = dist
                    far_node = v

                for u in adj[v]:
                    if u != parent and a[u] % p == 0:
                        stack.append((u, v, dist + 1))

            if size == 1:
                if answer < 1:
                    answer = 1
                continue

            # Second DFS: find the actual diameter of this component
            max_dist = 0
            stack = [(far_node, 0, 0)]

            while stack:
                v, parent, dist = stack.pop()
                if dist > max_dist:
                    max_dist = dist

                for u in adj[v]:
                    if u != parent and a[u] % p == 0:
                        stack.append((u, v, dist + 1))

            diameter_vertices = max_dist + 1
            if diameter_vertices > answer:
                answer = diameter_vertices

    print(answer)


if __name__ == "__main__":
    main()