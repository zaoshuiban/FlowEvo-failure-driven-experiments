import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])

    parent = list(range(26))
    present = [False] * 26

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    for s in data[1:n + 1]:
        first = s[0] - ord('a')
        present[first] = True

        for ch in s[1:]:
            x = ch - ord('a')
            present[x] = True
            union(first, x)

    components = set()
    for i in range(26):
        if present[i]:
            components.add(find(i))

    print(len(components))


if __name__ == "__main__":
    solve()