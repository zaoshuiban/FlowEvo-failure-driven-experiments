import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    parent = list(range(n))
    size = [1] * n
    degree = [0] * n

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
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2

        degree[u] += 1
        degree[v] += 1
        union(u, v)

    component_degree_sum = [0] * n

    for i in range(n):
        root = find(i)
        component_degree_sum[root] += degree[i]

    for i in range(n):
        if find(i) == i:
            expected = size[i] * (size[i] - 1)
            if component_degree_sum[i] != expected:
                print("NO")
                return

    print("YES")


if __name__ == "__main__":
    solve()