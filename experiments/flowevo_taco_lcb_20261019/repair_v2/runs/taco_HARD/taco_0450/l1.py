import sys

MOD = 1000000007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    d, n = data[0], data[1]
    a = [0] + data[2:2 + n]

    adj = [[] for _ in range(n + 1)]
    pos = 2 + n

    for _ in range(n - 1):
        u, v = data[pos], data[pos + 1]
        pos += 2
        adj[u].append(v)
        adj[v].append(u)

    sys.setrecursionlimit(1_000_000)

    answer = 0

    for root in range(1, n + 1):
        base = a[root]
        limit = base + d

        def dfs(u, parent):
            ways = 1

            for v in adj[u]:
                if v == parent:
                    continue

                if (
                    base <= a[v] <= limit
                    and (a[v] > base or v >= root)
                ):
                    ways = ways * (1 + dfs(v, u)) % MOD

            return ways

        answer = (answer + dfs(root, 0)) % MOD

    print(answer)


if __name__ == "__main__":
    main()