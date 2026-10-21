import sys


def solve() -> None:
    data = sys.stdin.readline().strip()
    if not data:
        return
    k = int(data)

    def c3(x: int) -> int:
        return x * (x - 1) * (x - 2) // 6

    # Largest clique size m such that C(m, 3) <= k
    m = 3
    while c3(m + 1) <= k:
        m += 1

    base = c3(m)
    rem = k - base

    def tri(x: int) -> int:
        return x * (x + 1) // 2

    # Any non-negative integer is a sum of three triangular numbers.
    tri_index = {}
    for a in range(m + 1):
        tri_index[tri(a)] = a

    extras = []
    if rem > 0:
        found = False
        for a in range(m + 1):
            for b in range(m + 1):
                left = rem - tri(a) - tri(b)
                if left >= 0 and left in tri_index:
                    c = tri_index[left]
                    extras = [x for x in (a, b, c) if x > 0]
                    found = True
                    break
            if found:
                break

    n = m + len(extras)
    adj = [['0'] * n for _ in range(n)]

    # Build a clique on the first m vertices.
    for i in range(m):
        for j in range(i + 1, m):
            adj[i][j] = adj[j][i] = '1'

    # Each extra vertex connected to x + 1 clique vertices creates tri(x) triangles.
    for idx, x in enumerate(extras):
        v = m + idx
        count = x + 1
        for u in range(count):
            adj[u][v] = adj[v][u] = '1'

    output = [str(n)]
    output.extend(''.join(row) for row in adj)
    sys.stdout.write('\n'.join(output))


if __name__ == "__main__":
    solve()