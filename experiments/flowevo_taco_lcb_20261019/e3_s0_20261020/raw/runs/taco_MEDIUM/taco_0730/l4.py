import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]  # number of edges
    parent = {}
    size = {}

    def find(x):
        if x not in parent:
            parent[x] = x
            size[x] = 1
            return x

        root = x
        while parent[root] != root:
            root = parent[root]

        # Path compression
        while parent[x] != x:
            nxt = parent[x]
            parent[x] = root
            x = nxt

        return root

    def union(a, b):
        ra = find(a)
        rb = find(b)

        if ra == rb:
            return

        if size[ra] < size[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        size[ra] += size[rb]

    idx = 1
    for _ in range(n):
        if idx + 1 >= len(data):
            break
        a = data[idx]
        b = data[idx + 1]
        idx += 2
        union(a, b)

    roots = set()
    for node in parent:
        roots.add(find(node))

    component_sizes = [size[root] for root in roots if size[root] >= 2]

    if component_sizes:
        print(min(component_sizes), max(component_sizes))
    else:
        print(0, 0)


if __name__ == "__main__":
    solve()