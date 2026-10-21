import sys

MOD = 10**9 + 7

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    k = next(it)

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

    for _ in range(n - 1):
        u = next(it) - 1
        v = next(it) - 1
        color = next(it)

        if color == 0:  # red edge
            union(u, v)

    bad = 0
    for i in range(n):
        if parent[i] == i:
            bad = (bad + pow(size[i], k, MOD)) % MOD

    total = pow(n, k, MOD)
    answer = (total - bad) % MOD
    print(answer)

if __name__ == "__main__":
    solve()