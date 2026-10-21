import sys

MOD = 10**9 + 7

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    knowledge = data[2:2 + n]

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

    idx = 2 + n
    for _ in range(m):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        union(u, v)

    component_max = {}
    component_count = {}

    for i in range(n):
        root = find(i)
        val = knowledge[i]

        if root not in component_max:
            component_max[root] = val
            component_count[root] = 1
        else:
            if val > component_max[root]:
                component_max[root] = val
                component_count[root] = 1
            elif val == component_max[root]:
                component_count[root] += 1

    answer = 1
    for count in component_count.values():
        answer = (answer * count) % MOD

    print(answer)

if __name__ == "__main__":
    solve()