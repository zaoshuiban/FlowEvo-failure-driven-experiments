import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    m = data[idx + 1]
    idx += 2

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
        k = data[idx]
        idx += 1

        if k == 0:
            continue

        first = data[idx] - 1
        idx += 1

        for _ in range(k - 1):
            user = data[idx] - 1
            idx += 1
            union(first, user)

    answer = [str(size[find(i)]) for i in range(n)]
    sys.stdout.write(" ".join(answer) + "\n")


if __name__ == "__main__":
    main()