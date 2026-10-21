import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])

    parent = list(range(26))
    size = [1] * 26

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

    seen = [False] * 26

    for s in data[1:n + 1]:
        first = None

        for ch in s:
            idx = ch - ord('a')
            seen[idx] = True

            if first is None:
                first = idx
            else:
                union(first, idx)

    roots = set()

    for i in range(26):
        if seen[i]:
            roots.add(find(i))

    print(len(roots))


if __name__ == "__main__":
    main()