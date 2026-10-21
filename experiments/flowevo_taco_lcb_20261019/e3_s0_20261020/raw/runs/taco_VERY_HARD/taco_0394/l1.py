import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    adj = [[] for _ in range(n + 1)]
    indegree = [0] * (n + 1)

    for _ in range(m):
        u = next(it)
        v = next(it)
        adj[u].append(v)
        indegree[v] += 1

    queue = deque(i for i in range(1, n + 1) if indegree[i] == 0)
    topo = []

    while queue:
        u = queue.popleft()
        topo.append(u)
        for v in adj[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    if len(topo) < n:
        print(-1)
        return

    out_min = [0] * (n + 1)

    for u in reversed(topo):
        mn = u
        for v in adj[u]:
            if out_min[v] < mn:
                mn = out_min[v]
        out_min[u] = mn

    in_min = list(range(n + 1))

    for u in topo:
        current_min = in_min[u]
        for v in adj[u]:
            if current_min < in_min[v]:
                in_min[v] = current_min

    answer = []
    universal_count = 0

    for i in range(1, n + 1):
        if out_min[i] == i and in_min[i] == i:
            answer.append('A')
            universal_count += 1
        else:
            answer.append('E')

    print(universal_count)
    print(''.join(answer))


if __name__ == "__main__":
    solve()