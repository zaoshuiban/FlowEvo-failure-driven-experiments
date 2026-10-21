import sys

def main():
    input = sys.stdin.buffer.readline

    n, m = map(int, input().split())

    parent = list(range(n + 1))
    size = [1] * (n + 1)
    degree = [0] * (n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra = find(a)
        rb = find(b)

        if ra == rb:
            return

        if size[ra] < size[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        size[ra] += size[rb]

    for _ in range(m):
        a, b = map(int, input().split())
        degree[a] += 1
        degree[b] += 1
        union(a, b)

    component_degree_sum = [0] * (n + 1)

    for v in range(1, n + 1):
        if degree[v] > 0:
            root = find(v)
            component_degree_sum[root] += degree[v]

    for v in range(1, n + 1):
        if find(v) == v:
            vertices = size[v]
            edges = component_degree_sum[v] // 2

            if edges != vertices * (vertices - 1) // 2:
                print("NO")
                return

    print("YES")


if __name__ == "__main__":
    main()