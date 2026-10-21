import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]

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

    idx = 2
    for _ in range(m):
        x = data[idx] - 1
        y = data[idx + 1] - 1
        idx += 2
        union(x, y)

    components = 0
    for i in range(n):
        if find(i) == i:
            components += 1

    answer = 1 << (n - components)
    print(answer)

if __name__ == "__main__":
    solve()