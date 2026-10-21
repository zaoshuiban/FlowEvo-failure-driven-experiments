import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    w = [0] + data[1:n + 1]

    m = n - 1
    edge_count = 2 * m

    head = [-1] * (n + 1)
    to = [0] * edge_count
    weight = [0] * edge_count
    nxt = [0] * edge_count

    pos = 1 + n
    idx = 0

    for _ in range(m):
        u = data[pos]
        v = data[pos + 1]
        c = data[pos + 2]
        pos += 3

        to[idx] = v
        weight[idx] = c
        nxt[idx] = head[u]
        head[u] = idx
        idx += 1

        to[idx] = u
        weight[idx] = c
        nxt[idx] = head[v]
        head[v] = idx
        idx += 1

    del data

    parent = [0] * (n + 1)
    parent[1] = -1

    order = []
    stack = [1]

    while stack:
        u = stack.pop()
        order.append(u)

        e = head[u]
        p = parent[u]

        while e != -1:
            v = to[e]
            if v != p:
                parent[v] = u
                stack.append(v)
            e = nxt[e]

    dp = w[:]
    answer = max(w[1:]) if n > 0 else 0

    for u in reversed(order):
        best1 = 0
        best2 = 0

        e = head[u]
        p = parent[u]

        while e != -1:
            v = to[e]
            if v != p:
                gain = dp[v] - weight[e]

                if gain > best1:
                    best2 = best1
                    best1 = gain
                elif gain > best2:
                    best2 = gain

            e = nxt[e]

        candidate = w[u] + best1 + best2
        if candidate > answer:
            answer = candidate

        dp[u] = w[u] + best1

    sys.stdout.write(str(answer) + "\n")


if __name__ == "__main__":
    solve()