import sys
from collections import deque


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    railway = [[False] * n for _ in range(n)]

    for _ in range(m):
        u = next(it) - 1
        v = next(it) - 1
        railway[u][v] = True
        railway[v][u] = True

    # If there is a direct railway from 1 to n, the train can arrive in 1 hour.
    # We only need the shortest road path for the bus.
    # Otherwise, the bus can reach n in 1 hour using a direct road,
    # and we only need the shortest railway path for the train.
    use_railway = not railway[0][n - 1]

    dist = [-1] * n
    dist[0] = 0
    queue = deque([0])

    while queue:
        u = queue.popleft()

        if u == n - 1:
            print(dist[u])
            return

        for v in range(n):
            if v == u or dist[v] != -1:
                continue

            edge_exists = railway[u][v] if use_railway else not railway[u][v]

            if edge_exists:
                dist[v] = dist[u] + 1
                queue.append(v)

    print(-1)


if __name__ == "__main__":
    main()