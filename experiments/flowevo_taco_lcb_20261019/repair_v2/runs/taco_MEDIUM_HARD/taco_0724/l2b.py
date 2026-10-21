import sys
from collections import deque


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0

    n = data[idx]
    idx += 1
    m = data[idx]
    idx += 1

    adj = [[] for _ in range(n + 1)]
    radj = [[] for _ in range(n + 1)]

    for _ in range(m):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        adj[u].append(v)
        radj[v].append(u)

    k = data[idx]
    idx += 1
    path = data[idx:idx + k]

    target = path[-1]

    dist = [-1] * (n + 1)
    dist[target] = 0
    q = deque([target])

    while q:
        v = q.popleft()
        nd = dist[v] + 1
        for u in radj[v]:
            if dist[u] == -1:
                dist[u] = nd
                q.append(u)

    minimum = 0
    maximum = 0

    for i in range(k - 1):
        cur = path[i]
        nxt = path[i + 1]

        if dist[nxt] != dist[cur] - 1:
            minimum += 1
            maximum += 1
        else:
            shortest_neighbors = 0
            needed_dist = dist[cur] - 1

            for v in adj[cur]:
                if dist[v] == needed_dist:
                    shortest_neighbors += 1
                    if shortest_neighbors > 1:
                        break

            if shortest_neighbors > 1:
                maximum += 1

    print(minimum, maximum)


if __name__ == "__main__":
    main()