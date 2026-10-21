import sys
from collections import deque

def solve():
    input = sys.stdin.buffer.readline
    n, m = map(int, input().split())

    adj = [[] for _ in range(n)]

    for _ in range(m):
        x, y = map(int, input().split())
        x -= 1
        y -= 1
        adj[x].append(y)
        adj[y].append(x)

    if n != m:
        print("NO")
        return

    visited = [False] * n
    queue = deque([0])
    visited[0] = True
    count = 0

    while queue:
        v = queue.popleft()
        count += 1

        for u in adj[v]:
            if not visited[u]:
                visited[u] = True
                queue.append(u)

    if count == n:
        print("FHTAGN!")
    else:
        print("NO")


if __name__ == "__main__":
    solve()