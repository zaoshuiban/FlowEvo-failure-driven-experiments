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

    if x1 == x2 and y1 == y2:
        print(0)
        return

    total = n * m
    start = x1 * m + y1
    target = x2 * m + y2

    # Precompute horizontal and vertical empty segment boundaries.
    row_left = array('i', [0]) * total
    row_right = array('i', [0]) * total
    col_up = array('i', [0]) * total
    col_down = array('i', [0]) * total

    for r in range(n):
        base = r * m
        row = grid[r]
        c = 0
        while c < m:
            if row[c] == 35:  # '#'
                c += 1
            else:
                seg_left = c
                while c < m and row[c] != 35:
                    c += 1
                seg_right = c - 1
                for j in range(seg_left, c):
                    idx = base + j
                    row_left[idx] = seg_left
                    row_right[idx] = seg_right

    for c in range(m):
        r = 0
        while r < n:
            if grid[r][c] == 35:  # '#'
                r += 1
            else:
                seg_up = r
                while r < n and grid[r][c] != 35:
                    r += 1
                seg_down = r - 1
                for i in range(seg_up, r):
                    idx = i * m + c
                    col_up[idx] = seg_up
                    col_down[idx] = seg_down

    dist = array('i', [-1]) * total
    dist[start] = 0

    # Successor DSU for rows and columns.
    row_size = n * (m + 1)
    col_size = m * (n + 1)
    row_parent = array('i', range(row_size))
    col_parent = array('i', range(col_size))

    def find_row(x):
        while row_parent[x] != x:
            row_parent[x] = row_parent[row_parent[x]]
            x = row_parent[x]
        return x

    def find_col(x):
        while col_parent[x] != x:
            col_parent[x] = col_parent[col_parent[x]]
            x = col_parent[x]
        return x

    # Remove the starting cell from DSUs.
    sx = x1 * (m + 1) + y1
    row_parent[sx] = find_row(sx + 1)

    sy = y1 * (n + 1) + x1
    col_parent[sy] = find_col(sy + 1)

    q = array('i', [start])
    head = 0
    append = q.append

    while head < len(q):
        idx = q[head]
        head += 1

        r = idx // m
        c = idx - r * m
        nd = dist[idx] + 1

        base_row = r * (m + 1)

        # Move right.
        left = c + 1
        right = c + k
        boundary = row_right[idx]
        if right > boundary:
            right = boundary

        if left <= right:
            x = find_row(base_row + left)
            end = base_row + right

            while x <= end:
                j = x - base_row
                nidx = r * m + j

                if nidx == target:
                    print(nd)
                    return

                dist[nidx] = nd

                nx = find_row(x + 1)
                row_parent[x] = nx

                y = j * (n + 1) + r
                ny = find_col(y + 1)
                col_parent[y] = ny

                append(nidx)
                x = nx

        # Move left.
        left = c - k
        boundary = row_left[idx]
        if left < boundary:
            left = boundary
        right = c - 1

        if left <= right:
            x = find_row(base_row + left)
            end = base_row + right

            while x <= end:
                j = x - base_row
                nidx = r * m + j

                if nidx == target:
                    print(nd)
                    return

                dist[nidx] = nd

                nx = find_row(x + 1)
                row_parent[x] = nx

                y = j * (n + 1) + r
                ny = find_col(y + 1)
                col_parent[y] = ny

                append(nidx)
                x = nx

        base_col = c * (n + 1)

        # Move down.
        up = r + 1
        down = r + k
        boundary = col_down[idx]
        if down > boundary:
            down = boundary

        if up <= down:
            x = find_col(base_col + up)
            end = base_col + down

            while x <= end:
                i = x - base_col
                nidx = i * m + c

                if nidx == target:
                    print(nd)
                    return

                dist[nidx] = nd

                nx = find_col(x + 1)
                col_parent[x] = nx

                ridx = i * (m + 1) + c
                nr = find_row(ridx + 1)
                row_parent[ridx] = nr

                append(nidx)
                x = nx

        # Move up.
        up = r - k
        boundary = col_up[idx]
        if up < boundary:
            up = boundary
        down = r - 1

        if up <= down:
            x = find_col(base_col + up)
            end = base_col + down

            while x <= end:
                i = x - base_col
                nidx = i * m + c

                if nidx == target:
                    print(nd)
                    return

                dist[nidx] = nd

                nx = find_col(x + 1)
                col_parent[x] = nx

                ridx = i * (m + 1) + c
                nr = find_row(ridx + 1)
                row_parent[ridx] = nr

                append(nidx)
                x = nx

    print(-1)


if __name__ == "__main__":
    main()