import sys


def solve() -> None:
    data = sys.stdin.readline().strip()
    if not data:
        return

    k = int(data)

    def c2(x: int) -> int:
        return x * (x - 1) // 2

    def c3(x: int) -> int:
        return x * (x - 1) * (x - 2) // 6

    # Take the largest clique whose number of triangles does not exceed k.
    a = 3
    while c3(a + 1) <= k:
        a += 1

    remaining = k - c3(a)

    # Values c2(t) for possible numbers t of clique neighbours.
    value_to_t = {}
    for t in range(a + 1):
        value_to_t.setdefault(c2(t), t)

    # By Gauss's theorem, remaining is a sum of at most three triangular numbers.
    found = None
    for t1 in range(a + 1):
        v1 = c2(t1)
        if v1 > remaining:
            break

        for t2 in range(a + 1):
            v2 = c2(t2)
            rem = remaining - v1 - v2

            if rem < 0:
                break

            if rem in value_to_t:
                found = (t1, t2, value_to_t[rem])
                break

        if found is not None:
            break

    # t = 0 and t = 1 both add zero triangles, so such vertices can be omitted.
    extra_neighbours = [t for t in found if t >= 2]

    n = a + len(extra_neighbours)
    graph = [['0'] * n for _ in range(n)]

    # Build the clique.
    for i in range(a):
        for j in range(a):
            if i != j:
                graph[i][j] = '1'

    # Add extra vertices, each connected to some vertices of the clique.
    for idx, t in enumerate(extra_neighbours):
        v = a + idx
        for u in range(t):
            graph[v][u] = '1'
            graph[u][v] = '1'

    result = [str(n)]
    for row in graph:
        result.append(''.join(row))

    sys.stdout.write('\n'.join(result))


if __name__ == "__main__":
    solve()