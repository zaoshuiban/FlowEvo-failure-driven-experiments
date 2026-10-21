import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    m = data[idx + 1]
    idx += 2

    forward = [[] for _ in range(n + 1)]
    reverse = [[] for _ in range(n + 1)]

    for _ in range(m):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        forward[u].append(v)
        reverse[v].append(u)

    k = data[idx]
    idx += 1
    path = data[idx:idx + k]

    target = path[-1]

    dist = [-1] * (n + 1)
    dist[target] = 0
    queue = deque([target])

    while queue:
        u = queue.popleft()
        next_dist = dist[u] + 1

        for v in reverse[u]:
            if dist[v] == -1:
                dist[v] = next_dist
                queue.append(v)

    minimum = 0
    maximum = 0

    for i in range(k - 1):
        u = path[i]
        v = path[i + 1]

        if dist[u] == dist[v] + 1:
            wanted_dist = dist[u] - 1
            has_alternative = False

            for nxt in forward[u]:
                if nxt != v and dist[nxt] == wanted_dist:
                    has_alternative = True
                    break

            if has_alternative:
                maximum += 1
        else:
            minimum += 1
            maximum += 1

    print(minimum, maximum)


if __name__ == "__main__":
    solve()