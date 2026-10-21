import sys

MOD = 10**9 + 7

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    knowledge = [0] + data[2:2 + n]

    parent = list(range(n + 1))
    size = [1] * (n + 1)

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
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        union(u, v)

    max_knowledge = [-1] * (n + 1)
    max_count = [0] * (n + 1)

    for i in range(1, n + 1):
        root = find(i)
        val = knowledge[i]

        if val > max_knowledge[root]:
            max_knowledge[root] = val
            max_count[root] = 1
        elif val == max_knowledge[root]:
            max_count[root] += 1

    answer = 1
    for i in range(1, n + 1):
        if max_count[i] > 0:
            answer = (answer * max_count[i]) % MOD

    print(answer)


if __name__ == "__main__":
    solve()