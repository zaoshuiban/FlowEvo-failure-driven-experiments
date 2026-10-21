import sys
from collections import deque

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    N = next(it)
    M = next(it)

    graph = [[] for _ in range(N)]

    for _ in range(M):
        a = next(it) - 1
        b = next(it) - 1
        x = next(it)
        y = next(it)

        graph[a].append((b, x, y))
        graph[b].append((a, -x, -y))

    pos = [None] * N
    pos[0] = (0, 0)

    queue = deque([0])

    while queue:
        v = queue.popleft()
        px, py = pos[v]

        for to, dx, dy in graph[v]:
            if pos[to] is None:
                pos[to] = (px + dx, py + dy)
                queue.append(to)

    answer = []

    for p in pos:
        if p is None:
            answer.append("undecidable")
        else:
            answer.append(f"{p[0]} {p[1]}")

    sys.stdout.write("\n".join(answer))

if __name__ == "__main__":
    main()