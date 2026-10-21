import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n, m = data[idx], data[idx + 1]
    idx += 2

    r = data[idx:idx + n]
    idx += n

    controlled = [[] for _ in range(n)]

    for switch in range(m):
        x = data[idx]
        idx += 1
        for _ in range(x):
            room = data[idx] - 1
            idx += 1
            controlled[room].append(switch)

    graph = [[] for _ in range(m)]

    for room in range(n):
        a, b = controlled[room]
        parity = r[room] ^ 1
        graph[a].append((b, parity))
        graph[b].append((a, parity))

    color = [-1] * m

    for start in range(m):
        if color[start] != -1:
            continue

        color[start] = 0
        stack = [start]

        while stack:
            u = stack.pop()

            for v, parity in graph[u]:
                expected = color[u] ^ parity

                if color[v] == -1:
                    color[v] = expected
                    stack.append(v)
                elif color[v] != expected:
                    print("NO")
                    return

    print("YES")


if __name__ == "__main__":
    solve()