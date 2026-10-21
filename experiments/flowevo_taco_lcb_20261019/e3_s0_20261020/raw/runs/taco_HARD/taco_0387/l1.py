import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, q = data[0], data[1], data[2]
    total_vertices = n + m

    parent = list(range(total_vertices))
    size = [1] * total_vertices
    components = total_vertices

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    idx = 3
    for _ in range(q):
        r = data[idx] - 1
        c = data[idx + 1] - 1
        idx += 2

        a = r
        b = n + c

        ra = find(a)
        rb = find(b)

        if ra != rb:
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            size[ra] += size[rb]
            components -= 1

    print(components - 1)


if __name__ == "__main__":
    solve()