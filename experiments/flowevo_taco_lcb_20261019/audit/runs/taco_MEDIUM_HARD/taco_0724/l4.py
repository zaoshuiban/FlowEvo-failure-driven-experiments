import sys
from collections import deque


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1
    m = data[idx]
    idx += 1

    adj = [[] for _ in range(n + 1)]
    rev_adj = [[] for _ in range(n + 1)]

    for _ in range(m):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        adj[u].append(v)
        rev_adj[v].append(u)

    k = data[idx]
    idx += 1
    path = data[idx:idx + k]

    target = path[-1]

    # dist[v] = shortest distance from v to target
    dist = [-1] * (n + 1)
    dist[target] = 0
    q = deque([target])

    while q:
        v = q.popleft()
        for u in rev_adj[v]:
            if dist[u] == -1:
                dist[u] = dist[v] + 1
                q.append(u)

    minimum = 0
    maximum = 0

    for i in range(k - 1):
        cur = path[i]
        nxt = path[i + 1]

        if dist[cur] != dist[nxt] + 1:
            minimum += 1
            maximum += 1
        else:
            needed = dist[cur] - 1
            count = 0

            for v in adj[cur]:
                if dist[v] == needed:
                    count += 1
                    if count > 1:
                        break

            if count > 1:
                maximum += 1

    print(minimum, maximum)


if __name__ == "__main__":
    solve()