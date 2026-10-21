import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    parent = list(range(n + 1))
    size = [1] * (n + 1)
    degree = [0] * (n + 1)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra = find(a)
        rb = find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]

    idx = 2
    for _ in range(m):
        u = data[idx]
        v = data[idx + 1]
        idx += 2

        degree[u] += 1
        degree[v] += 1
        union(u, v)

    bad = [False] * (n + 1)

    for v in range(1, n + 1):
        if degree[v] != 2:
            bad[find(v)] = True

    answer = 0

    for v in range(1, n + 1):
        if parent[v] == v and not bad[v]:
            answer += 1

    print(answer)


if __name__ == "__main__":
    solve()