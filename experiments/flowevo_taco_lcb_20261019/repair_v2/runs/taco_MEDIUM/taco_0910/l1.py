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

    idx = 2
    for _ in range(m):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        degree[a] += 1
        degree[b] += 1

        ra = find(a)
        rb = find(b)

        if ra != rb:
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            size[ra] += size[rb]

    component_degree = [0] * (n + 1)

    for v in range(1, n + 1):
        root = find(v)
        component_degree[root] += degree[v]

    for root in range(1, n + 1):
        if parent[root] == root:
            vertices = size[root]
            if component_degree[root] != vertices * (vertices - 1):
                print("NO")
                return

    print("YES")


if __name__ == "__main__":
    solve()