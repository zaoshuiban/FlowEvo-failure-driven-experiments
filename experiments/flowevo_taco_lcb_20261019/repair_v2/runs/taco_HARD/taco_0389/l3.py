import sys
from array import array


def main():
    input = sys.stdin.buffer.readline

    n, m, k = map(int, input().split())
    grid = [input().strip() for _ in range(n)]

    x1, y1, x2, y2 = map(int, input().split())
    x1 -= 1
    y1 -= 1
    x2 -= 1
    y2 -= 1

    start = x1 * m + y1
    target = x2 * m + y2

    if start == target:
        print(0)
        return

    total = n * m
    dist = array('i', [-1]) * total
    dist[start] = 0

    q = array('i', [start])
    head = 0
    append = q.append

    while head < len(q):
        idx = q[head]
        head += 1

        nd = dist[idx] + 1
        r = idx // m
        c = idx - r * m
        base = r * m

        # Right
        limit = c + k
        if limit >= m:
            limit = m - 1

        nidx = idx + 1
        for j in range(c + 1, limit + 1):
            if grid[r][j] == 35:  # '#'
                break

            val = dist[nidx]
            if val == -1:
                if nidx == target:
                    print(nd)
                    return
                dist[nidx] = nd
                append(nidx)
            elif val < nd:
                break

            nidx += 1

        # Left
        low = c - k
        if low < 0:
            low = 0

        nidx = idx - 1
        for j in range(c - 1, low - 1, -1):
            if grid[r][j] == 35:
                break

            val = dist[nidx]
            if val == -1:
                if nidx == target:
                    print(nd)
                    return
                dist[nidx] = nd
                append(nidx)
            elif val < nd:
                break

            nidx -= 1

        # Down
        limit = r + k
        if limit >= n:
            limit = n - 1

        nidx = idx + m
        for i in range(r + 1, limit + 1):
            if grid[i][c] == 35:
                break

            val = dist[nidx]
            if val == -1:
                if nidx == target:
                    print(nd)
                    return
                dist[nidx] = nd
                append(nidx)
            elif val < nd:
                break

            nidx += m

        # Up
        low = r - k
        if low < 0:
            low = 0

        nidx = idx - m
        for i in range(r - 1, low - 1, -1):
            if grid[i][c] == 35:
                break

            val = dist[nidx]
            if val == -1:
                if nidx == target:
                    print(nd)
                    return
                dist[nidx] = nd
                append(nidx)
            elif val < nd:
                break

            nidx -= m

    print(-1)


if __name__ == "__main__":
    main()