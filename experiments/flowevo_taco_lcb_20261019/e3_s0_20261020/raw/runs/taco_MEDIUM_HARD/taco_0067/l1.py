import sys
from collections import deque

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    adj = [[] for _ in range(n)]
    degree = [0] * n

    idx = 1
    for _ in range(n):
        x = data[idx] - 1
        y = data[idx + 1] - 1
        idx += 2

        adj[x].append(y)
        adj[y].append(x)
        degree[x] += 1
        degree[y] += 1

    removed = [False] * n
    queue = deque()

    for i in range(n):
        if degree[i] == 1:
            queue.append(i)

    while queue:
        u = queue.popleft()

        if removed[u]:
            continue

        removed[u] = True

        for v in adj[u]:
            if not removed[v]:
                degree[v] -= 1
                if degree[v] == 1:
                    queue.append(v)

    dist = [-1] * n
    queue = deque()

    for i in range(n):
        if not removed[i]:
            dist[i] = 0
            queue.append(i)

    while queue:
        u = queue.popleft()

        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                queue.append(v)

    print(" ".join(map(str, dist)))


if __name__ == "__main__":
    main()