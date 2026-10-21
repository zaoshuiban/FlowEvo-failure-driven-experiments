import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]

    blue = [0] * (n + 1)
    has_red = bytearray(n + 1)

    root = 0
    total_blue = 0

    for i in range(1, n + 1):
        c = data[i]
        if c == 1:
            has_red[i] = 1
            if root == 0:
                root = i
        elif c == 2:
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
    append_order = order.append

    for v in order:
        pv = parent[v]
        for u in adj[v]:
            if u != pv:
                parent[u] = v
                append_order(u)

    ans = 0

    for i in range(n - 1, 0, -1):
        v = order[i]

        if blue[v] == total_blue and has_red[v] == 0:
            ans += 1

        p = parent[v]

        if has_red[v]:
            has_red[p] = 1

        blue[p] += blue[v]

    sys.stdout.write(str(ans) + "\n")


if __name__ == "__main__":
    main()