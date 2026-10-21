import sys


def int_iter():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False

    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_num = True
        elif in_num:
            yield num
            num = 0
            in_num = False

    if in_num:
        yield num


def solve() -> None:
    it = int_iter()

    try:
        m = next(it)
    except StopIteration:
        return

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

    del it, a, b

    edges.sort(reverse=True)

    vertex_count = m + n
    parent = [-1] * vertex_count

    def find(x: int) -> int:
        root = x
        while parent[root] >= 0:
            root = parent[root]

        while x != root:
            nxt = parent[x]
            parent[x] = root
            x = nxt

        return root

    max_forest_weight = 0
    used_edges = 0
    needed_edges = vertex_count - 1

    for weight, u, v in edges:
        ru = find(u)
        rv = find(v)

        if ru == rv:
            continue

        if parent[ru] > parent[rv]:
            ru, rv = rv, ru

        parent[ru] += parent[rv]
        parent[rv] = ru

        max_forest_weight += weight
        used_edges += 1

        if used_edges == needed_edges:
            break

    print(total_cost - max_forest_weight)


if __name__ == "__main__":
    solve()