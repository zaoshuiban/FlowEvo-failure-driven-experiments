import sys


def c2(x: int) -> int:
    return x * (x - 1) // 2


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    k = int(data[0])

    # Choose the largest m such that K_m has at most k triangles.
    m = 3
    while (m + 1) * m * (m - 1) // 6 <= k:
        m += 1

    base_triangles = m * (m - 1) * (m - 2) // 6
    rem = k - base_triangles

    # Represent rem as c2(a) + c2(b) + c2(c).
    rep = None
    for a in range(m + 1):
        ca = c2(a)
        if ca > rem:
            break

        for b in range(m + 1):
            cb = c2(b)
            if ca + cb > rem:
                break

            need = rem - ca - cb

            for c in range(m + 1):
                cc = c2(c)
                if cc == need:
                    rep = (a, b, c)
                    break
                if cc > need:
                    break

            if rep is not None:
                break

        if rep is not None:
            break

    # Each extra vertex is connected to a vertices of the base clique.
    # It creates exactly C(a, 2) triangles.
    extras = [x for x in rep if x >= 2]

    n = m + len(extras)
    graph = [['0'] * n for _ in range(n)]

    def add_edge(u: int, v: int) -> None:
        graph[u][v] = '1'
        graph[v][u] = '1'

    # Base clique.
    for i in range(m):
        for j in range(i + 1, m):
            add_edge(i, j)

    # Extra independent vertices.
    for idx, a in enumerate(extras):
        v = m + idx
        for j in range(a):
            add_edge(v, j)

    output = [str(n)]
    output.extend(''.join(row) for row in graph)
    sys.stdout.write('\n'.join(output))


if __name__ == "__main__":
    main()