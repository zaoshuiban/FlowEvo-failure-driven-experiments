import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [0] + data[1:n + 1]

    indeg = [0] * (n + 1)
    for i in range(1, n + 1):
        indeg[a[i]] += 1

    q = deque(i for i in range(1, n + 1) if indeg[i] == 0)

    while q:
        u = q.popleft()
        v = a[u]
        indeg[v] -= 1
        if indeg[v] == 0:
            q.append(v)

    visited = [False] * (n + 1)
    cycles = []

    for i in range(1, n + 1):
        if indeg[i] > 0 and not visited[i]:
            cur = i
            cycle = []
            while not visited[cur]:
                visited[cur] = True
                cycle.append(cur)
                cur = a[cur]
            cycles.append(cycle)

    root = -1

    for cycle in cycles:
        if len(cycle) == 1 and a[cycle[0]] == cycle[0]:
            root = cycle[0]
            break

    changes = 0

    if root != -1:
        for cycle in cycles:
            if len(cycle) == 1 and cycle[0] == root:
                continue

            v = cycle[0]
            a[v] = root
            changes += 1
    else:
        first_cycle = cycles[0]
        root = first_cycle[0]

        a[root] = root
        changes += 1

        for i in range(1, len(cycles)):
            v = cycles[i][0]
            a[v] = root
            changes += 1

    print(changes)
    print(" ".join(map(str, a[1:])))


if __name__ == "__main__":
    solve()