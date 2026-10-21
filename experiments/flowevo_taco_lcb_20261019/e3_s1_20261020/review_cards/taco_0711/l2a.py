import sys

MOD = 10**9 + 7

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    knowledge = [next(it) for _ in range(n)]

    parent = [-1] * n

    def find(x):
        while parent[x] >= 0:
            if parent[parent[x]] >= 0:
                parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx = find(x)
        ry = find(y)

        if rx == ry:
            return

        if parent[rx] > parent[ry]:
            rx, ry = ry, rx

        parent[rx] += parent[ry]
        parent[ry] = rx

    for _ in range(m):
        u = next(it) - 1
        v = next(it) - 1
        union(u, v)

    max_value = {}
    count = {}

    for i in range(n):
        root = find(i)
        val = knowledge[i]

        if root not in max_value:
            max_value[root] = val
            count[root] = 1
        elif val > max_value[root]:
            max_value[root] = val
            count[root] = 1
        elif val == max_value[root]:
            count[root] += 1

    answer = 1
    for c in count.values():
        answer = (answer * c) % MOD

    print(answer)


if __name__ == "__main__":
    solve()