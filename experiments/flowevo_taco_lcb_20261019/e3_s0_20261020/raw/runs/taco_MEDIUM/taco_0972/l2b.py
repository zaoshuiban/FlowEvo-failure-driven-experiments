import sys
from array import array

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, k = data[0], data[1], data[2]
    INF = 10000

    dist = [array('H', [INF]) * m for _ in range(n)]

    idx = 3
    for _ in range(k):
        x = data[idx] - 1
        y = data[idx + 1] - 1
        idx += 2
        dist[x][y] = 0

    # First pass: top-left to bottom-right
    for i in range(n):
        row = dist[i]
        has_up = i > 0
        if has_up:
            up = dist[i - 1]

        for j in range(m):
            best = row[j]

            if has_up:
                value = up[j] + 1
                if value < best:
                    best = value

            if j > 0:
                value = row[j - 1] + 1
                if value < best:
                    best = value

            row[j] = best

    # Second pass: bottom-right to top-left
    max_dist = -1
    ans_x = ans_y = 0

    for i in range(n - 1, -1, -1):
        row = dist[i]
        has_down = i + 1 < n
        if has_down:
            down = dist[i + 1]

        for j in range(m - 1, -1, -1):
            best = row[j]

            if has_down:
                value = down[j] + 1
                if value < best:
                    best = value

            if j + 1 < m:
                value = row[j + 1] + 1
                if value < best:
                    best = value

            row[j] = best

            if best > max_dist:
                max_dist = best
                ans_x = i + 1
                ans_y = j + 1

    print(ans_x, ans_y)


if __name__ == "__main__":
    solve()