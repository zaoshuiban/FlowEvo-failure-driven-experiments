import sys
from collections import deque

def solve():
    input = sys.stdin.buffer.readline
    T = int(input())
    answers = []
    INF = 10**9
    DOT = ord('.')

    for _ in range(T):
        N, M = map(int, input().split())
        grid = [input().strip() for _ in range(N)]

        total_cells = N * M
        base = total_cells
        V = total_cells + N

        dist = [INF] * V
        visited = bytearray(V)

        start = 0
        dist[start] = 0
        dq = deque([start])

        target_cell = total_cells - 1
        target_row = base + N - 1

        while dq:
            u = dq.popleft()

            if visited[u]:
                continue
            visited[u] = 1

            du = dist[u]

            if u < total_cells:
                i = u // M
                j = u - i * M
                row = grid[i]

                if row[j] != DOT:
                    continue

                # Move to adjacent empty cells, cost 0
                if i > 0 and grid[i - 1][j] == DOT:
                    v = u - M
                    if du < dist[v]:
                        dist[v] = du
                        dq.appendleft(v)

                if i + 1 < N and grid[i + 1][j] == DOT:
                    v = u + M
                    if du < dist[v]:
                        dist[v] = du
                        dq.appendleft(v)

                if j > 0 and row[j - 1] == DOT:
                    v = u - 1
                    if du < dist[v]:
                        dist[v] = du
                        dq.appendleft(v)

                if j + 1 < M and row[j + 1] == DOT:
                    v = u + 1
                    if du < dist[v]:
                        dist[v] = du
                        dq.appendleft(v)

                # Select row i or an adjacent row, cost 1
                nd = du + 1

                v = base + i
                if nd < dist[v]:
                    dist[v] = nd
                    dq.append(v)

                if i > 0:
                    v = base + i - 1
                    if nd < dist[v]:
                        dist[v] = nd
                        dq.append(v)

                if i + 1 < N:
                    v = base + i + 1
                    if nd < dist[v]:
                        dist[v] = nd
                        dq.append(v)

            else:
                # Row node: row r has been selected
                r = u - base
                row_start = r * M

                # Access empty cells in the selected row, cost 0
                row = grid[r]
                for j, ch in enumerate(row):
                    if ch == DOT:
                        v = row_start + j
                        if du < dist[v]:
                            dist[v] = du
                            dq.appendleft(v)

                nd = du + 1

                # Access empty cells in row r - 1, or select row r - 1
                if r > 0:
                    up_start = row_start - M
                    up = grid[r - 1]

                    for j, ch in enumerate(up):
                        if ch == DOT:
                            v = up_start + j
                            if du < dist[v]:
                                dist[v] = du
                                dq.appendleft(v)

                    v = base + r - 1
                    if nd < dist[v]:
                        dist[v] = nd
                        dq.append(v)

                # Access empty cells in row r + 1, or select row r + 1
                if r + 1 < N:
                    down_start = row_start + M
                    down = grid[r + 1]

                    for j, ch in enumerate(down):
                        if ch == DOT:
                            v = down_start + j
                            if du < dist[v]:
                                dist[v] = du
                                dq.appendleft(v)

                    v = base + r + 1
                    if nd < dist[v]:
                        dist[v] = nd
                        dq.append(v)

        ans = dist[target_row]

        if grid[N - 1][M - 1] == DOT:
            ans = min(ans, dist[target_cell])

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()