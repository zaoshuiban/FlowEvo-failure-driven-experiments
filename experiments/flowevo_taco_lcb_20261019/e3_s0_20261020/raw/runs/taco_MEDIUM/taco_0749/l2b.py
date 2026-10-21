import sys


def main() -> None:
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    m = next(data)

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
        k = next(data)

        if k == 0:
            continue

        first = next(data) - 1

        for _ in range(k - 1):
            union(first, next(data) - 1)

    answer = [str(size[find(i)]) for i in range(n)]
    sys.stdout.write(" ".join(answer) + "\n")


if __name__ == "__main__":
    main()