import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    colors = data[1:1 + n]

    adj = [[] for _ in range(n)]
    idx = 1 + n
    for _ in range(n - 1):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        adj[u].append(v)
        adj[v].append(u)

    total_red = colors.count(1)
    total_blue = colors.count(2)

    sub_red = [0] * n
    sub_blue = [0] * n

    for i, color in enumerate(colors):
        if color == 1:
            sub_red[i] = 1
        elif color == 2:
            sub_blue[i] = 1

    parent = [-1] * n
    parent[0] = 0

    order = []
    stack = [0]

    while stack:
        v = stack.pop()
        order.append(v)

        for u in adj[v]:
            if u != parent[v]:
                parent[u] = v
                stack.append(u)

    answer = 0

    for v in reversed(order):
        r = sub_red[v]
        b = sub_blue[v]

        if v != 0:
            if (r == total_red and b == 0) or (b == total_blue and r == 0):
                answer += 1

            p = parent[v]
            sub_red[p] += r
            sub_blue[p] += b

    print(answer)


if __name__ == "__main__":
    solve()