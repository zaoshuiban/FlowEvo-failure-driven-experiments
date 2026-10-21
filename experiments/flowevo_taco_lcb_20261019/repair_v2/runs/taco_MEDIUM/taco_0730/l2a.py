import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]

    parent = {}
    size = {}

    def add(x):
        if x not in parent:
            parent[x] = x
            size[x] = 1

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]

        while parent[x] != x:
            nxt = parent[x]
            parent[x] = root
            x = nxt

        return root

    def union(a, b):
        add(a)
        add(b)

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
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        union(u, v)

    if not parent:
        print("0 0")
        return

    roots = set()
    for node in parent:
        roots.add(find(node))

    smallest = min(size[root] for root in roots if size[root] >= 2)
    largest = max(size[root] for root in roots if size[root] >= 2)

    print(smallest, largest)


if __name__ == "__main__":
    solve()