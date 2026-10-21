import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

    parent = list(range(n))
    size = [1] * n
    edges = []

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    idx = 2
    for _ in range(m):
        a = data[idx] - 1
        b = data[idx + 1] - 1
        idx += 2
        edges.append((a, b))

        ra = find(a)
        rb = find(b)

        if ra != rb:
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            size[ra] += size[rb]

    edge_count = [0] * n

    for a, b in edges:
        edge_count[find(a)] += 1

    for i in range(n):
        if parent[i] == i:
            required_edges = size[i] * (size[i] - 1) // 2
            if edge_count[i] != required_edges:
                print("NO")
                return

    print("YES")


if __name__ == "__main__":
    main()