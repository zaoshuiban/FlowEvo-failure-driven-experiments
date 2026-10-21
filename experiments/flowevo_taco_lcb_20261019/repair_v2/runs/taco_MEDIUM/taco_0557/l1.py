import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)
    k = next(it)

    governments = [next(it) - 1 for _ in range(k)]

    parent = list(range(n))
    size = [1] * n

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

    for _ in range(m):
        u = next(it) - 1
        v = next(it) - 1
        union(u, v)

    government_roots = set(find(g) for g in governments)

    total_government_vertices = 0
    max_government_component = 0
    government_component_edges = 0

    for root in government_roots:
        component_size = size[root]
        total_government_vertices += component_size
        max_government_component = max(max_government_component, component_size)
        government_component_edges += component_size * (component_size - 1) // 2

    free_vertices = n - total_government_vertices

    max_component_edges = max_government_component * (max_government_component - 1) // 2
    merged_component_edges = (
        (max_government_component + free_vertices)
        * (max_government_component + free_vertices - 1)
        // 2
    )

    maximum_edges = (
        government_component_edges
        - max_component_edges
        + merged_component_edges
    )

    print(maximum_edges - m)


if __name__ == "__main__":
    solve()