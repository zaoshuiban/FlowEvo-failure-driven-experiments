import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    parent = list(range(n + 1))
    size = [1] * (n + 1)

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

    edges = []
    idx = 2

    for _ in range(m):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        edges.append((a, b))
        union(a, b)

    edge_count = [0] * (n + 1)

    for a, b in edges:
        root = find(a)
        edge_count[root] += 1

    for v in range(1, n + 1):
        if find(v) == v:
            vertices = size[v]
            required_edges = vertices * (vertices - 1) // 2

            if edge_count[v] != required_edges:
                print("NO")
                return

    print("YES")


if __name__ == "__main__":
    main()