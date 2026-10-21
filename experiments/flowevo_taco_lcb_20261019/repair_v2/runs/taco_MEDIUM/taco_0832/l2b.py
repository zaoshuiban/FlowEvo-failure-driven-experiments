import sys
from collections import deque

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    adj = [[] for _ in range(n)]

    idx = 2
    for _ in range(m):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        adj[u].append(v)
        adj[v].append(u)

    color = [-1] * n

    for start in range(n):
        if color[start] != -1:
            continue

        color[start] = 0
        q = deque([start])

        while q:
            u = q.popleft()
            for v in adj[u]:
                if color[v] == -1:
                    color[v] = color[u] ^ 1
                    q.append(v)
                elif color[v] == color[u]:
                    print(-1)
                    return

    a = [i + 1 for i in range(n) if color[i] == 0]
    b = [i + 1 for i in range(n) if color[i] == 1]

    out = []
    out.append(str(len(a)))
    out.append(" ".join(map(str, a)))
    out.append(str(len(b)))
    out.append(" ".join(map(str, b)))

    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    solve()