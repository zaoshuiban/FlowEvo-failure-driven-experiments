import sys
from collections import deque


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    T = int(next(it))
    DOT = ord('.')
    INF = 10**9
    answers = []

    for _ in range(T):
        N = int(next(it))
        M = int(next(it))
        grid = [next(it) for _ in range(N)]

        K = N * M
        V = K + N

        dist = [INF] * V
        visited = bytearray(V)
        dq = deque([0])
        dist[0] = 0

        if grid[N - 1][M - 1] == DOT:
            target = (N - 1) * M + (M - 1)
        else:
            target = K + (N - 1)

        answer = 0

        while dq:
            v = dq.popleft()

            if visited[v]:
                continue
            visited[v] = 1

            d = dist[v]

            if v == target:
                answer = d
                break

            if v < K:
                r = v // M
                c = v - r * M

                if r > 0:
                    u = v - M
                    if grid[r - 1][c] == DOT and d < dist[u]:
                        dist[u] = d
                        dq.appendleft(u)

                if r + 1 < N:
                    u = v + M
                    if grid[r + 1][c] == DOT and d < dist[u]:
                        dist[u] = d
                        dq.appendleft(u)

                if c > 0:
                    u = v - 1
                    if grid[r][c - 1] == DOT and d < dist[u]:
                        dist[u] = d
                        dq.appendleft(u)

                if c + 1 < M:
                    u = v + 1
                    if grid[r][c + 1] == DOT and d < dist[u]:
                        dist[u] = d
                        dq.appendleft(u)

                nd = d + 1

                rr = r - 1
                if rr >= 0:
                    u = K + rr
                    if nd < dist[u]:
                        dist[u] = nd
                        dq.append(u)

                u = K + r
                if nd < dist[u]:
                    dist[u] = nd
                    dq.append(u)

                rr = r + 1
                if rr < N:
                    u = K + rr
                    if nd < dist[u]:
                        dist[u] = nd
                        dq.append(u)

            else:
                rr = v - K
                nd = d + 1

                if rr > 0:
                    u = v - 1
                    if nd < dist[u]:
                        dist[u] = nd
                        dq.append(u)

                if rr + 1 < N:
                    u = v + 1
                    if nd < dist[u]:
                        dist[u] = nd
                        dq.append(u)

                r0 = rr - 1
                if r0 < 0:
                    r0 = 0

                r1 = rr + 1
                if r1 >= N:
                    r1 = N - 1

                for r2 in range(r0, r1 + 1):
                    row = grid[r2]
                    base = r2 * M

                    for c2, ch in enumerate(row):
                        if ch == DOT:
                            u = base + c2
                            if d < dist[u]:
                                dist[u] = d
                                dq.appendleft(u)

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()