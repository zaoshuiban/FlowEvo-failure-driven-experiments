import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    colors = data[1:1 + n]

    adj = [[] for _ in range(n + 1)]
    idx = 1 + n
    for _ in range(n - 1):
        v = data[idx]
        u = data[idx + 1]
        idx += 2
        adj[v].append(u)
        adj[u].append(v)

    red = [0] * (n + 1)
    blue = [0] * (n + 1)

    total_red = 0
    total_blue = 0

    for i, color in enumerate(colors, start=1):
        if color == 1:
            red[i] = 1
            total_red += 1
        elif color == 2:
            blue[i] = 1
            total_blue += 1

    parent = [0] * (n + 1)
    parent[1] = -1

    order = [1]
    for v in order:
        for u in adj[v]:
            if u != parent[v]:
                parent[u] = v
                order.append(u)

    answer = 0

    for v in reversed(order):
        if v == 1:
            continue

        rv = red[v]
        bv = blue[v]

        if (rv == total_red and bv == 0) or (bv == total_blue and rv == 0):
            answer += 1

        p = parent[v]
        red[p] += rv
        blue[p] += bv

    print(answer)


if __name__ == "__main__":
    main()