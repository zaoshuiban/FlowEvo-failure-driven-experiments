import sys
from collections import deque

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    g = [bytearray(n) for _ in range(n)]

    idx = 2
    for _ in range(m):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        g[u][v] = 1
        g[v][u] = 1

    # Build the complement graph.
    h = [[] for _ in range(n)]
    for i in range(n):
        gi = g[i]
        for j in range(i + 1, n):
            if not gi[j]:
                h[i].append(j)
                h[j].append(i)

    start = -1
    for i in range(n):
        if h[i]:
            start = i
            break

    # The original graph is complete, so all vertices may have the same letter.
    if start == -1:
        sys.stdout.write("Yes\n" + "a" * n + "\n")
        return

    color = [-1] * n
    color[start] = 0
    q = deque([start])

    cnt = [0, 0]
    degree_sum = 0

    while q:
        v = q.popleft()
        cnt[color[v]] += 1
        degree_sum += len(h[v])

        for to in h[v]:
            if color[to] == -1:
                color[to] = color[v] ^ 1
                q.append(to)
            elif color[to] == color[v]:
                sys.stdout.write("No\n")
                return

    # All non-isolated vertices in the complement must belong to one component.
    for i in range(n):
        if h[i] and color[i] == -1:
            sys.stdout.write("No\n")
            return

    edges = degree_sum // 2
    if edges != cnt[0] * cnt[1]:
        sys.stdout.write("No\n")
        return

    answer = []
    for i in range(n):
        if h[i]:
            answer.append('a' if color[i] == 0 else 'c')
        else:
            answer.append('b')

    sys.stdout.write("Yes\n" + ''.join(answer) + "\n")


if __name__ == "__main__":
    solve()