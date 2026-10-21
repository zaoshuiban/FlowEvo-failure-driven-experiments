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
        first = None

        for ch in s:
            letter = ch - ord('a')
            present[letter] = True

            if first is None:
                first = letter
            else:
                union(first, letter)

    answer = 0

    for i in range(26):
        if present[i] and find(i) == i:
            answer += 1

    print(answer)


if __name__ == "__main__":
    solve()