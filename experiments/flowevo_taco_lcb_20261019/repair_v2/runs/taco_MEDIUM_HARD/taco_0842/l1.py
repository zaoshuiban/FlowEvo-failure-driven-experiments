import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    idx = 1

    w = [0] * (n + 1)
    for i in range(1, n + 1):
        w[i] = data[idx]
        idx += 1

    adj = [[] for _ in range(n + 1)]
    for _ in range(n - 1):
        u = data[idx]
        v = data[idx + 1]
        c = data[idx + 2]
        idx += 3
        adj[u].append((v, c))
        adj[v].append((u, c))

    del data

    parent = [0] * (n + 1)
    parent[1] = -1
    order = [1]

    for u in order:
        for v, _ in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)

    dp = [0] * (n + 1)
    answer = 0

    for u in reversed(order):
        best1 = 0
        best2 = 0

        for v, c in adj[u]:
            if parent[v] == u:
                value = dp[v] - c
                if value > best1:
                    best2 = best1
                    best1 = value
                elif value > best2:
                    best2 = value

        dp[u] = w[u] + best1
        answer = max(answer, w[u] + best1 + best2)

    print(answer)


if __name__ == "__main__":
    solve()