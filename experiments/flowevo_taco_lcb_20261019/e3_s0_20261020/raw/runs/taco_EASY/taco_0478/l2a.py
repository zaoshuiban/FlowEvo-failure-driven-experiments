import sys

MOD = 1_000_000_007

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    risk = [0] + data[idx:idx + n]
    idx += n

    k = data[idx]
    idx += 1

    parent = list(range(n + 1))
    rank = [0] * (n + 1)

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
        if rank[ra] < rank[rb]:
            parent[ra] = rb
        elif rank[ra] > rank[rb]:
            parent[rb] = ra
        else:
            parent[rb] = ra
            rank[ra] += 1

    for _ in range(k):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        union(u, v)

    component_min = {}
    component_count = {}

    for city in range(1, n + 1):
        root = find(city)
        value = risk[city]

        if root not in component_min:
            component_min[root] = value
            component_count[root] = 1
        elif value < component_min[root]:
            component_min[root] = value
            component_count[root] = 1
        elif value == component_min[root]:
            component_count[root] += 1

    answer = 1
    for count in component_count.values():
        answer = (answer * count) % MOD

    print(answer)

if __name__ == "__main__":
    solve()