import sys


def ints_from_bytes(data):
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


def main():
    data = sys.stdin.buffer.read()
    it = ints_from_bytes(data)

    n = next(it)
    m = next(it)

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
        k = next(it)
        if k == 0:
            continue

        first = next(it) - 1
        for _ in range(k - 1):
            user = next(it) - 1
            union(first, user)

    answer = [str(size[find(i)]) for i in range(n)]
    sys.stdout.write(" ".join(answer))


if __name__ == "__main__":
    main()