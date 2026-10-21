import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]

    blue = [0] * (n + 1)
    has_red = bytearray(n + 1)

    root = 0
    total_blue = 0

    for i in range(1, n + 1):
        color = data[i]
        if color == 1:
            has_red[i] = 1
            if root == 0:
                root = i
        elif color == 2:
            blue[i] = 1
            total_blue += 1

    adj = [[] for _ in range(n + 1)]

    idx = n + 1
    for _ in range(n - 1):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        adj[u].append(v)
        adj[v].append(u)

    parent = [0] * (n + 1)
    parent[root] = -1

    order = [root]
    ptr = 0

    while ptr < len(order):
        v = order[ptr]
        ptr += 1

        for u in adj[v]:
            if u != parent[v]:
                parent[u] = v
                order.append(u)

    answer = 0

    for i in range(len(order) - 1, 0, -1):
        v = order[i]

        if blue[v] == total_blue and has_red[v] == 0:
            answer += 1

        p = parent[v]
        blue[p] += blue[v]

        if has_red[v]:
            has_red[p] = 1

    sys.stdout.write(str(answer) + "\n")


if __name__ == "__main__":
    main()