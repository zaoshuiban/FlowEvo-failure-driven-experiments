import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    idx = 1

    colors = data[idx:idx + n]
    idx += n

    graph = [[] for _ in range(n)]

    for _ in range(n - 1):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        graph[u].append(v)
        graph[v].append(u)

    total_red = colors.count(1)
    total_blue = colors.count(2)

    parent = [-1] * n
    parent[0] = 0
    order = [0]

    for v in order:
        for to in graph[v]:
            if parent[to] == -1:
                parent[to] = v
                order.append(to)

    red = [0] * n
    blue = [0] * n

    for i, color in enumerate(colors):
        if color == 1:
            red[i] = 1
        elif color == 2:
            blue[i] = 1

    for v in reversed(order):
        p = parent[v]
        if p != v:
            red[p] += red[v]
            blue[p] += blue[v]

    answer = 0

    for v in range(n):
        if parent[v] == v:
            continue

        r = red[v]
        b = blue[v]

        if (r == total_red and b == 0) or (b == total_blue and r == 0):
            answer += 1

    print(answer)


if __name__ == "__main__":
    solve()