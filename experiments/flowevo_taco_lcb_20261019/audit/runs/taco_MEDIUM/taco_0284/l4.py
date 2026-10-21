import sys


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])

    parent = list(range(26))
    size = [1] * 26
    used = [False] * 26

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

    for s in data[1:1 + n]:
        chars = list(set(s))

        for c in chars:
            used[c - ord('a')] = True

        if len(chars) > 1:
            base = chars[0] - ord('a')
            for c in chars[1:]:
                union(base, c - ord('a'))

    roots = set()
    for i in range(26):
        if used[i]:
            roots.add(find(i))

    print(len(roots))


if __name__ == "__main__":
    solve()