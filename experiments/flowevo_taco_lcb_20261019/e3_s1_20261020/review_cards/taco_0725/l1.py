import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    m = next(it)

    initial = [next(it) for _ in range(n)]
    controlled_by = [[] for _ in range(n)]

    for switch in range(m):
        cnt = next(it)
        for _ in range(cnt):
            room = next(it) - 1
            controlled_by[room].append(switch)

    graph = [[] for _ in range(m)]

    for room in range(n):
        a, b = controlled_by[room]
        # Need: initial[room] XOR x[a] XOR x[b] = 1
        # Therefore: x[a] XOR x[b] = 1 XOR initial[room]
        required = 1 ^ initial[room]
        graph[a].append((b, required))
        graph[b].append((a, required))

    color = [-1] * m

    for start in range(m):
        if color[start] != -1:
            continue

        color[start] = 0
        queue = deque([start])

        while queue:
            u = queue.popleft()

            for v, required in graph[u]:
                expected = color[u] ^ required

                if color[v] == -1:
                    color[v] = expected
                    queue.append(v)
                elif color[v] != expected:
                    print("NO")
                    return

    print("YES")


if __name__ == "__main__":
    solve()