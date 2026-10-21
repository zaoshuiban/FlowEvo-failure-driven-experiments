import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    adj = [[] for _ in range(n)]

    for _ in range(m):
        a = next(it) - 1
        b = next(it) - 1
        c = next(it)

        # Required XOR between operation counts of a and b:
        # c XOR x_a XOR x_b = 1  =>  x_a XOR x_b = 1 - c
        w = 1 - c

        adj[a].append((b, w))
        adj[b].append((a, w))

    color = [-1] * n
    possible = True

    for start in range(n):
        if color[start] != -1:
            continue

        color[start] = 0
        q = deque([start])

        while q:
            u = q.popleft()

            for v, w in adj[u]:
                required = color[u] ^ w

                if color[v] == -1:
                    color[v] = required
                    q.append(v)
                elif color[v] != required:
                    possible = False
                    break

            if not possible:
                break

        if not possible:
            break

    if not possible:
        sys.stdout.write("Impossible")
        return

    answer = [str(i + 1) for i in range(n) if color[i] == 1]

    sys.stdout.write(str(len(answer)) + "\n")
    sys.stdout.write(" ".join(answer))


if __name__ == "__main__":
    solve()