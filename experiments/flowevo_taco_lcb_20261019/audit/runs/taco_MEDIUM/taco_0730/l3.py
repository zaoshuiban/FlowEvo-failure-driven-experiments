import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

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

    # The first integer is the number of listed edges.
    # Processing all remaining pairs is also robust to equivalent input formats.
    for i in range(1, len(data) - 1, 2):
        union(data[i], data[i + 1])

    roots = set()
    for node in list(parent.keys()):
        roots.add(find(node))

    component_sizes = [size[root] for root in roots if size[root] >= 2]

    if component_sizes:
        print(min(component_sizes), max(component_sizes))
    else:
        print(0, 0)


if __name__ == "__main__":
    main()