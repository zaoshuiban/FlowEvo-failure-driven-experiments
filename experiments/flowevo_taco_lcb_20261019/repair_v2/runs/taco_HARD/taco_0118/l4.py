import sys
from collections import deque
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
    limit = isqrt(max_a)
    for i in range(2, limit + 1):
        if spf[i] == i:
            for j in range(i * i, max_a + 1, i):
                if spf[j] == j:
                    spf[j] = i

    # Vertices grouped by every prime dividing their value
    by_prime = {}
    for v in range(1, n + 1):
        x = a[v]
        while x > 1:
            p = spf[x]
            by_prime.setdefault(p, []).append(v)
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

            # First BFS: find one diameter endpoint of this component
            q = deque([(start, 0)])
            visited[start] = stamp
            far_node = start
            far_dist = 0

            while q:
                v, dist = q.popleft()
                if dist > far_dist:
                    far_dist = dist
                    far_node = v

                for u in adj[v]:
                    if visited[u] != stamp and a[u] % p == 0:
                        visited[u] = stamp
                        q.append((u, dist + 1))

            # Second BFS: compute the diameter of the component
            q = deque([(far_node, 0, 0)])
            diameter_edges = 0

            while q:
                v, parent, dist = q.popleft()
                if dist > diameter_edges:
                    diameter_edges = dist

                for u in adj[v]:
                    if u != parent and a[u] % p == 0:
                        q.append((u, v, dist + 1))

            answer = max(answer, diameter_edges + 1)

    print(answer)


if __name__ == "__main__":
    main()