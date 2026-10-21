import sys


def main():
    input = sys.stdin.buffer.readline

    first = input().split()
    if not first:
        return

    n = int(first[0])
    m = int(first[1])

    parent = list(range(n + 1))
    size = [1] * (n + 1)
    edge_count = [0] * (n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for _ in range(m):
        a, b = map(int, input().split())

        ra = find(a)
        rb = find(b)

        if ra == rb:
            edge_count[ra] += 1
        else:
            if size[ra] < size[rb]:
                ra, rb = rb, ra

            parent[rb] = ra
            size[ra] += size[rb]
            edge_count[ra] += edge_count[rb] + 1

    for v in range(1, n + 1):
        if parent[v] == v:
            vertices = size[v]
            required_edges = vertices * (vertices - 1) // 2

            if edge_count[v] != required_edges:
                print("NO")
                return

    print("YES")


if __name__ == "__main__":
    main()