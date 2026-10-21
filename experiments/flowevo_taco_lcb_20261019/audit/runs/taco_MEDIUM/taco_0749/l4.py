import sys


def read_ints():
    data = sys.stdin.buffer.read()
    num = 0
    inside = False

    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            inside = True
        else:
            if inside:
                yield num
                num = 0
                inside = False

    if inside:
        yield num


def main() -> None:
    it = iter(read_ints())

    try:
        n = next(it)
        m = next(it)
    except StopIteration:
        return

    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return

        if size[root_a] < size[root_b]:
            root_a, root_b = root_b, root_a

        parent[root_b] = root_a
        size[root_a] += size[root_b]

    for _ in range(m):
        k = next(it)

        if k == 0:
            continue

        first = next(it) - 1

        for _ in range(k - 1):
            user = next(it) - 1
            union(first, user)

    answer = [str(size[find(i)]) for i in range(n)]
    sys.stdout.write(" ".join(answer) + "\n")


if __name__ == "__main__":
    main()