import sys
from collections import deque


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1
    m = data[idx]
    idx += 1

    r = data[idx:idx + n]
    idx += n

    first_switch = [-1] * n
    graph = [[] for _ in range(m)]

    for switch in range(m):
        cnt = data[idx]
        idx += 1

        for _ in range(cnt):
            room = data[idx] - 1
            idx += 1

            if first_switch[room] == -1:
                first_switch[room] = switch
            else:
                other = first_switch[room]
                required = r[room] ^ 1

                graph[switch].append((other, required))
                graph[other].append((switch, required))

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