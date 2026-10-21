import sys


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])

    parent = list(range(26))
    size = [1] * 26
    present = [False] * 26

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

    for i in range(1, n + 1):
        s = data[i]
        first = s[0] - ord('a')

        for ch in s:
            present[ch - ord('a')] = True

        for ch in s[1:]:
            union(first, ch - ord('a'))

    answer = 0

    for i in range(26):
        if present[i] and find(i) == i:
            answer += 1

    print(answer)


if __name__ == "__main__":
    solve()