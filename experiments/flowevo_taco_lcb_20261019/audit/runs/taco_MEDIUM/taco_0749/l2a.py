import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    n = int(next(it))
    m = int(next(it))

    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra = find(a)
        rb = find(b)

        if ra == rb:
            return

        if size[ra] < size[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        size[ra] += size[rb]

    for _ in range(m):
        k = int(next(it))
        if k == 0:
            continue

        first = int(next(it)) - 1

        for _ in range(k - 1):
            user = int(next(it)) - 1
            union(first, user)

    answer = [str(size[find(i)]) for i in range(n)]
    sys.stdout.write(" ".join(answer))


if __name__ == "__main__":
    solve()