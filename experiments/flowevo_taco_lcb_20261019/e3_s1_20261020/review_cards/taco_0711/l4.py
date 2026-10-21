import sys

MOD = 10**9 + 7

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    knowledge = data[2:2 + n]
    idx = 2 + n

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

    for _ in range(m):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        union(u, v)

    max_knowledge = [-10**18] * n
    max_count = [0] * n

    for i in range(n):
        root = find(i)
        val = knowledge[i]

        if val > max_knowledge[root]:
            max_knowledge[root] = val
            max_count[root] = 1
        elif val == max_knowledge[root]:
            max_count[root] += 1

    answer = 1
    for i in range(n):
        if parent[i] == i:
            answer = (answer * max_count[i]) % MOD

    print(answer)


if __name__ == "__main__":
    solve()