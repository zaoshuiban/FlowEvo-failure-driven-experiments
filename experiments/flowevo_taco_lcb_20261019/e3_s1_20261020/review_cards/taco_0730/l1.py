import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    total_nodes = 2 * n

    parent = list(range(total_nodes + 1))
    size = [1] * (total_nodes + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return

        if size[root_a] < size[root_b]:
            root_a, root_b = root_b, root_a

        parent[root_b] = root_a
        size[root_a] += size[root_b]

    idx = 1
    for _ in range(n):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        union(u, v)

    smallest = float("inf")
    largest = 0

    for node in range(1, total_nodes + 1):
        if parent[node] == node and size[node] >= 2:
            smallest = min(smallest, size[node])
            largest = max(largest, size[node])

    print(int(smallest), largest)


if __name__ == "__main__":
    main()