import sys
from collections import deque

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    m = next(it)

    forward = [[] for _ in range(n)]
    reverse = [[] for _ in range(n)]

    for _ in range(m):
        u = next(it) - 1
        v = next(it) - 1
        forward[u].append(v)
        reverse[v].append(u)

    k = next(it)
    path = [next(it) - 1 for _ in range(k)]

    t = path[-1]

    dist = [-1] * n
    dist[t] = 0
    q = deque([t])

    while q:
        u = q.popleft()
        for v in reverse[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                q.append(v)

    minimum = 0
    maximum = 0

    for i in range(k - 1):
        u = path[i]
        v = path[i + 1]

        if dist[u] != dist[v] + 1:
            minimum += 1
            maximum += 1
        else:
            target = dist[u] - 1
            count = 0

            for nxt in forward[u]:
                if dist[nxt] == target:
                    count += 1
                    if count > 1:
                        break

            if count > 1:
                maximum += 1

    print(minimum, maximum)


if __name__ == "__main__":
    main()