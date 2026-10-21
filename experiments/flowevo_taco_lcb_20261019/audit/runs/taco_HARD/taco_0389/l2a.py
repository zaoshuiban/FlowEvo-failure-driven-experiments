import sys
from array import array


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    n = int(next(it))
    m = int(next(it))
    k = int(next(it))

    rows = [next(it) for _ in range(n)]

    x1 = int(next(it)) - 1
    y1 = int(next(it)) - 1
    x2 = int(next(it)) - 1
    y2 = int(next(it)) - 1

    start_idx = x1 * m + y1
    target_idx = x2 * m + y2

    if start_idx == target_idx:
        print(0)
        return

    total = n * m

    row_l = array('H', [0]) * total
    row_r = array('H', [0]) * total

    for r in range(n):
        row = rows[r]
        base = r * m
        c = 0
        while c < m:
            if row[c] == 46:  # '.'
                start = c
                c += 1
                while c < m and row[c] == 46:
                    c += 1
                end = c - 1
                for j in range(start, end + 1):
                    row_l[base + j] = start
                    row_r[base + j] = end
            else:
                c += 1

    col_u = array('H', [0]) * total
    col_d = array('H', [0]) * total

    for c in range(m):
        r = 0
        while r < n:
            if rows[r][c] == 46:
                start = r
                r += 1
                while r < n and rows[r][c] == 46:
                    r += 1
                end = r - 1
                for i in range(start, end + 1):
                    idx = i * m + c
                    col_u[idx] = start
                    col_d[idx] = end
            else:
                r += 1

    row_stride = m + 1
    nxt_row = array('H', [0]) * (n * row_stride)

    for r in range(n):
        base = r * row_stride
        nxt_row[base + m] = m
        nxt_val = m
        row = rows[r]
        for c in range(m - 1, -1, -1):
            if row[c] == 46:
                nxt_val = c
            nxt_row[base + c] = nxt_val

    col_stride = n + 1
    nxt_col = array('H', [0]) * (m * col_stride)

    for c in range(m):
        base = c * col_stride
        nxt_col[base + n] = n
        nxt_val = n
        for r in range(n - 1, -1, -1):
            if rows[r][c] == 46:
                nxt_val = r
            nxt_col[base + r] = nxt_val

    def find_row(r, c, nr=nxt_row, stride=row_stride):
        base = r * stride
        x = c
        while nr[base + x] != x:
            nr[base + x] = nr[base + nr[base + x]]
            x = nr[base + x]
        return x

    def find_col(c, r, nc=nxt_col, stride=col_stride):
        base = c * stride
        x = r
        while nc[base + x] != x:
            nc[base + x] = nc[base + nc[base + x]]
            x = nc[base + x]
        return x

    base = x1 * row_stride
    nxt_row[base + y1] = find_row(x1, y1 + 1)

    base = y1 * col_stride
    nxt_col[base + x1] = find_col(y1, x1 + 1)

    queue = [start_idx]
    distance = 0

    while queue:
        next_queue = []
        next_distance = distance + 1

        for idx in queue:
            r = idx // m
            c = idx - r * m

            left = c - k
            if left < row_l[idx]:
                left = row_l[idx]

            right = c + k
            if right > row_r[idx]:
                right = row_r[idx]

            base_r = r * row_stride
            col = find_row(r, left)

            while col <= right:
                if r * m + col == target_idx:
                    print(next_distance)
                    return

                nxt = find_row(r, col + 1)
                nxt_row[base_r + col] = nxt

                base_c = col * col_stride
                nxt_col[base_c + r] = find_col(col, r + 1)

                next_queue.append(r * m + col)
                col = nxt

            top = r - k
            if top < col_u[idx]:
                top = col_u[idx]

            bottom = r + k
            if bottom > col_d[idx]:
                bottom = col_d[idx]

            base_c = c * col_stride
            rr = find_col(c, top)

            while rr <= bottom:
                if rr * m + c == target_idx:
                    print(next_distance)
                    return

                base_r = rr * row_stride
                nxt_row[base_r + c] = find_row(rr, c + 1)

                nxt = find_col(c, rr + 1)
                nxt_col[base_c + rr] = nxt

                next_queue.append(rr * m + c)
                rr = nxt

        distance = next_distance
        queue = next_queue

    print(-1)


if __name__ == "__main__":
    solve()