import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    m = data[idx]
    n = data[idx + 1]
    idx += 2

    a = data[idx:idx + m]
    idx += m

    b = data[idx:idx + n]
    idx += n

    edges = []
    total_cost = 0

    for i in range(m):
        s = data[idx]
        idx += 1
        ai = a[i]

        for _ in range(s):
            j = data[idx] - 1
            idx += 1

            weight = ai + b[j]
            total_cost += weight
            edges.append((weight, i, m + j))

    edges.sort(reverse=True)

    vertex_count = m + n
    parent = list(range(vertex_count))
    size = [1] * vertex_count

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    max_forest_weight = 0
    used_edges = 0

    for weight, u, v in edges:
        ru = find(u)
        rv = find(v)

        if ru == rv:
            continue

        if size[ru] < size[rv]:
            ru, rv = rv, ru

        parent[rv] = ru
        size[ru] += size[rv]

        max_forest_weight += weight
        used_edges += 1

        if used_edges == vertex_count - 1:
            break

    print(total_cost - max_forest_weight)


if __name__ == "__main__":
    solve()