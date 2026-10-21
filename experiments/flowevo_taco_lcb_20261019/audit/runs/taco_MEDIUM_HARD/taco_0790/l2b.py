import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [x - 1 for x in data[1:1 + n]]

    main_root = -1
    for i in range(n):
        if a[i] == i:
            main_root = i
            break

    ans = 0

    if main_root == -1:
        indeg = [0] * n
        for v in a:
            indeg[v] += 1

        q = deque(i for i in range(n) if indeg[i] == 0)

        while q:
            u = q.popleft()
            v = a[u]
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

        for i in range(n):
            if indeg[i] > 0:
                main_root = i
                break

        a[main_root] = main_root
        ans = 1

    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx = find(x)
        ry = find(y)
        if rx == ry:
            return
        if size[rx] < size[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        size[rx] += size[ry]

    for i in range(n):
        if i == main_root:
            continue

        ai = a[i]

        if ai == i or find(i) == find(ai):
            a[i] = main_root
            ans += 1
            union(i, main_root)
        else:
            union(i, ai)

    print(ans)
    print(*[x + 1 for x in a])


if __name__ == "__main__":
    solve()