import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    adj = [[False] * n for _ in range(n)]
    degree = [0] * n

    idx = 2
    for _ in range(m):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2

        adj[u][v] = adj[v][u] = True
        degree[u] += 1
        degree[v] += 1

    # A complete graph can be represented using only letter 'a'.
    if all(degree[i] == n - 1 for i in range(n)):
        print("Yes")
        print("a" * n)
        return

    labels = ["?"] * n

    # Vertices connected to everyone must be 'b' in any non-complete valid graph.
    for i in range(n):
        if degree[i] == n - 1:
            labels[i] = "b"

    start = -1
    for i in range(n):
        if labels[i] == "?":
            start = i
            break

    if start == -1:
        print("Yes")
        print("a" * n)
        return

    # In the complement graph, the remaining vertices must form one connected
    # complete bipartite graph, whose parts will get letters 'a' and 'c'.
    color = [-1] * n
    color[start] = 0

    q = deque([start])

    while q:
        u = q.popleft()

        for v in range(n):
            if u == v or labels[v] != "?":
                continue

            # Edge in complement graph
            if not adj[u][v]:
                if color[v] == -1:
                    color[v] = 1 - color[u]
                    q.append(v)
                elif color[v] == color[u]:
                    print("No")
                    return

    # The non-'b' part must be connected in the complement graph.
    for i in range(n):
        if labels[i] == "?":
            if color[i] == -1:
                print("No")
                return
            labels[i] = "a" if color[i] == 0 else "c"

    value = {"a": 0, "b": 1, "c": 2}

    # Verify that the constructed string produces exactly the given graph.
    for i in range(n):
        for j in range(i + 1, n):
            should_be_edge = abs(value[labels[i]] - value[labels[j]]) <= 1
            if should_be_edge != adj[i][j]:
                print("No")
                return

    print("Yes")
    print("".join(labels))


if __name__ == "__main__":
    solve()