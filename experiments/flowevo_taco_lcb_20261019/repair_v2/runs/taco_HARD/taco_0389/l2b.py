import sys
from collections import deque
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

    if x1 == x2 and y1 == y2:
        print(0)
        return

    row_size = m + 1
    col_size = n + 1

    # DSU structures for next/previous available cells in rows and columns.
    row_right = array('i', range(n * row_size))
    row_left = array('i', range(n * row_size))
    col_down = array('i', range(m * col_size))
    col_up = array('i', range(m * col_size))

    def find(parent, x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def erase(r, c):
        base_r = r * row_size

        idx = base_r + c
        row_right[idx] = find(row_right, idx + 1)

        idx2 = base_r + c + 1
        row_left[idx2] = find(row_left, idx2 - 1)

        base_c = c * col_size

        idxd = base_c + r
        col_down[idxd] = find(col_down, idxd + 1)

        idxu = base_c + r + 1
        col_up[idxu] = find(col_up, idxu - 1)

    q = deque()
    append = q.append
    popleft = q.popleft

    erase(x1, y1)
    append(x1 * m + y1)

    dist = 0

    while q:
        for _ in range(len(q)):
            idx = popleft()
            r = idx // m
            c = idx - r * m

            # Right
            base_r = r * row_size
            limit = c + k
            if limit >= m:
                limit = m - 1

            x = c + 1
            while x <= limit:
                root = find(row_right, base_r + x)
                p = root - base_r

                if p > limit:
                    break
                if grid[r][p] == 35:  # '#'
                    break

                if r == x2 and p == y2:
                    print(dist + 1)
                    return

                erase(r, p)
                append(r * m + p)
                x = p + 1

            # Left
            low = c - k
            if low < 0:
                low = 0

            x = c - 1
            while x >= low:
                root = find(row_left, base_r + x + 1)
                p = root - base_r - 1

                if p < low:
                    break
                if grid[r][p] == 35:
                    break

                if r == x2 and p == y2:
                    print(dist + 1)
                    return

                erase(r, p)
                append(r * m + p)
                x = p - 1

            # Down
            base_c = c * col_size
            limit = r + k
            if limit >= n:
                limit = n - 1

            x = r + 1
            while x <= limit:
                root = find(col_down, base_c + x)
                p = root - base_c

                if p > limit:
                    break
                if grid[p][c] == 35:
                    break

                if p == x2 and c == y2:
                    print(dist + 1)
                    return

                erase(p, c)
                append(p * m + c)
                x = p + 1

            # Up
            low = r - k
            if low < 0:
                low = 0

            x = r - 1
            while x >= low:
                root = find(col_up, base_c + x + 1)
                p = root - base_c - 1

                if p < low:
                    break
                if grid[p][c] == 35:
                    break

                if p == x2 and c == y2:
                    print(dist + 1)
                    return

                erase(p, c)
                append(p * m + c)
                x = p - 1

        dist += 1

    print(-1)


if __name__ == "__main__":
    main()