import sys


def solve() -> None:
    it = iter(map(int, sys.stdin.buffer.read().split()))

    m = next(it)
    n = next(it)

    a = [next(it) for _ in range(m)]
    b = [next(it) for _ in range(n)]

    edges = []
    total_cost = 0

    for i in range(m):
        s = next(it)
        ai = a[i]

        for _ in range(s):
            j = next(it) - 1
            weight = ai + b[j]
            total_cost += weight
            edges.append((weight, i, m + j))

    edges.sort(reverse=True)

    parent = list(range(m + n))
    size = [1] * (m + n)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    max_forest_weight = 0
    used_edges = 0
    vertices = m + n

    for weight, u, v in edges:
        ru = find(u)
        rv = find(v)

        if ru != rv:
            if size[ru] < size[rv]:
                ru, rv = rv, ru

            parent[rv] = ru
            size[ru] += size[rv]

            max_forest_weight += weight
            used_edges += 1

            if used_edges == vertices - 1:
                break

    print(total_cost - max_forest_weight)


if __name__ == "__main__":
    solve()