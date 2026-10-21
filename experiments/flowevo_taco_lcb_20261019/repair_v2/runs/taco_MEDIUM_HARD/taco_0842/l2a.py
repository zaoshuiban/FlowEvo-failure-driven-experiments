import sys


def solve() -> None:
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int() -> int:
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    n = next_int()

    w = [0] * (n + 1)
    for i in range(1, n + 1):
        w[i] = next_int()

    adj = [[] for _ in range(n + 1)]

    for _ in range(n - 1):
        u = next_int()
        v = next_int()
        c = next_int()
        adj[u].append((v, c))
        adj[v].append((u, c))

    parent = [0] * (n + 1)
    parent[1] = -1

    order = []
    stack = [1]

    while stack:
        u = stack.pop()
        order.append(u)

        for v, _ in adj[u]:
            if v != parent[u]:
                parent[v] = u
                stack.append(v)

    dp = [0] * (n + 1)
    answer = 0

    for u in reversed(order):
        best1 = 0
        best2 = 0

        for v, cost in adj[u]:
            if v != parent[u]:
                value = dp[v] - cost

                if value > best1:
                    best2 = best1
                    best1 = value
                elif value > best2:
                    best2 = value

        dp[u] = w[u] + best1
        answer = max(answer, w[u] + best1 + best2)

    sys.stdout.write(str(answer))


if __name__ == "__main__":
    solve()