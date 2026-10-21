import sys

MOD = 10**9 + 7

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    e = [0] + data[idx:idx + n]
    idx += n

    k = data[idx]
    idx += 1

    parent = list(range(n + 1))
    rank = [0] * (n + 1)

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

        if rank[ra] < rank[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1

    for _ in range(k):
        a = data[idx]
        b = data[idx + 1]
        idx += 2
        union(a, b)

    INF = 10**18
    min_cost = [INF] * (n + 1)
    count = [0] * (n + 1)

    for city in range(1, n + 1):
        root = find(city)
        cost = e[city]

        if cost < min_cost[root]:
            min_cost[root] = cost
            count[root] = 1
        elif cost == min_cost[root]:
            count[root] += 1

    answer = 1

    for root in range(1, n + 1):
        if min_cost[root] != INF:
            answer = (answer * count[root]) % MOD

    print(answer)


if __name__ == "__main__":
    solve()