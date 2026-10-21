import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    m = next(it)
    n = next(it)

    a = [next(it) for _ in range(m)]
    b = [next(it) for _ in range(n)]

    edges = []
    total_cost = 0

    for i in range(m):
        s = next(it)
        for _ in range(s):
            x = next(it) - 1
            w = a[i] + b[x]
            total_cost += w
            edges.append((w, i, m + x))

    edges.sort(reverse=True)

    parent = list(range(m + n))
    size = [1] * (m + n)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    saved = 0

    for w, u, v in edges:
        ru = find(u)
        rv = find(v)

        if ru != rv:
            if size[ru] < size[rv]:
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]
            saved += w

    print(total_cost - saved)


if __name__ == "__main__":
    solve()