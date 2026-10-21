import sys
from array import array

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, k = data[0], data[1], data[2]
    INF = 10000
    size = n * m

    # dist[r * m + c] = minimum Manhattan distance to any initial fire
    dist = array('H', [INF]) * size

    idx = 3
    for _ in range(k):
        x = data[idx] - 1
        y = data[idx + 1] - 1
        idx += 2
        dist[x * m + y] = 0

    # First pass: from top-left to bottom-right
    for i in range(n):
        base = i * m
        up_base = base - m if i > 0 else -1
        for j in range(m):
            pos = base + j
            best = dist[pos]

            if i > 0:
                v = dist[up_base + j] + 1
                if v < best:
                    best = v

            if j > 0:
                v = dist[pos - 1] + 1
                if v < best:
                    best = v

            dist[pos] = best

    # Second pass: from bottom-right to top-left
    max_dist = -1
    ans_x = ans_y = 0

    for i in range(n - 1, -1, -1):
        base = i * m
        down_base = base + m if i + 1 < n else -1

        for j in range(m - 1, -1, -1):
            pos = base + j
            best = dist[pos]

            if i + 1 < n:
                v = dist[down_base + j] + 1
                if v < best:
                    best = v

            if j + 1 < m:
                v = dist[pos + 1] + 1
                if v < best:
                    best = v

            dist[pos] = best

            if best > max_dist:
                max_dist = best
                ans_x = i + 1
                ans_y = j + 1

    print(ans_x, ans_y)


if __name__ == "__main__":
    solve()