import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    colors = data[idx:idx + n]
    idx += n

    preds = [[] for _ in range(n)]
    children = [[] for _ in range(n)]
    indeg = [0] * n

    for i in range(n):
        k = data[idx]
        idx += 1

        indeg[i] = k
        for _ in range(k):
            p = data[idx] - 1
            idx += 1
            preds[i].append(p)
            children[p].append(i)

    queue = deque(i for i in range(n) if indeg[i] == 0)
    topo = []

    while queue:
        v = queue.popleft()
        topo.append(v)

        for nxt in children[v]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)

    best_travel = 10**18

    for start_level in (1, 2, 3):
        level = [0] * n
        min_level = 10**18
        max_level = -10**18

        for v in topo:
            lower = start_level

            for p in preds[v]:
                if level[p] > lower:
                    lower = level[p]

            residue = colors[v] % 3
            val = lower + ((residue - lower) % 3)

            level[v] = val
            min_level = min(min_level, val)
            max_level = max(max_level, val)

        best_travel = min(best_travel, max_level - min_level)

    print(n + best_travel)


if __name__ == "__main__":
    solve()