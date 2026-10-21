import sys
from collections import deque

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    colors = [next(it) - 1 for _ in range(n)]

    pred = [[] for _ in range(n)]
    succ = [[] for _ in range(n)]

    for i in range(n):
        k = next(it)
        for _ in range(k):
            u = next(it) - 1
            pred[i].append(u)
            succ[u].append(i)

    indeg = [len(pred[i]) for i in range(n)]
    q = deque(i for i in range(n) if indeg[i] == 0)
    topo = []

    while q:
        u = q.popleft()
        topo.append(u)
        for v in succ[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

    def feasible(limit: int) -> bool:
        for shift in range(3):
            pos = [0] * n
            ok = True

            for v in topo:
                base = 0
                for u in pred[v]:
                    if pos[u] > base:
                        base = pos[u]

                rem = (colors[v] + shift) % 3
                x = base + ((rem - base) % 3)

                if x > limit:
                    ok = False
                    break

                pos[v] = x

            if ok:
                return True

        return False

    lo = -1
    hi = 3 * n + 5

    while hi - lo > 1:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid

    print(n + hi)


if __name__ == "__main__":
    solve()