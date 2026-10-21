import sys
from collections import deque


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)

    color = [next(it) for _ in range(n)]

    succ = [[] for _ in range(n)]
    indeg0 = [0] * n

    for i in range(n):
        k = next(it)
        indeg0[i] = k
        for _ in range(k):
            prerequisite = next(it) - 1
            succ[prerequisite].append(i)

    best_movement = 10**9

    for lower_bound in (1, 2, 3):
        indeg = indeg0[:]
        time = [0] * n
        required = [lower_bound] * n
        q = deque()

        for i in range(n):
            if indeg[i] == 0:
                r = color[i] % 3
                time[i] = lower_bound + ((r - lower_bound) % 3)
                q.append(i)

        while q:
            u = q.popleft()
            tu = time[u]

            for v in succ[u]:
                if tu > required[v]:
                    required[v] = tu

                indeg[v] -= 1
                if indeg[v] == 0:
                    r = color[v] % 3
                    x = required[v]
                    time[v] = x + ((r - x) % 3)
                    q.append(v)

        movement = max(time) - min(time)
        if movement < best_movement:
            best_movement = movement

    print(n + best_movement)


if __name__ == "__main__":
    main()