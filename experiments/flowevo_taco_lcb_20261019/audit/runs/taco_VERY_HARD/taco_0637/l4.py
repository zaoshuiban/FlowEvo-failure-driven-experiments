import sys
from collections import deque
from array import array


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answer_lines = []

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        x = int(data[idx]) - 1
        y = int(data[idx + 1]) - 1
        idx += 2

        cells = n * m
        grid = bytearray(cells)

        for r in range(n):
            row = bytearray()
            while len(row) < m:
                row.extend(data[idx])
                idx += 1

            base = r * m
            for c in range(m):
                if row[c] == 49:  # '1'
                    grid[base + c] = 1

        # State layout:
        # [0, cells)                         : standing on one cell
        # [base_h, base_v)                   : lying horizontally, covers (r,c),(r,c+1)
        # [base_v, total_states)             : lying vertically, covers (r,c),(r+1,c)
        base_h = cells
        h_count = n * (m - 1)
        base_v = base_h + h_count
        v_count = (n - 1) * m
        total_states = cells + h_count + v_count

        dist = array('i', [-1]) * total_states

        start = x * m + y
        dist[start] = 0

        q = deque([start])
        append = q.append
        popleft = q.popleft

        h_row_len = m - 1

        while q:
            cur = popleft()
            nd = dist[cur] + 1

            if cur < cells:
                # Standing
                r = cur // m
                c = cur - r * m
                row_base = r * m

                # Roll north -> vertical lying at rows r-2, r-1
                if r >= 2:
                    if grid[(r - 1) * m + c] and grid[(r - 2) * m + c]:
                        nxt = base_v + (r - 2) * m + c
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll south -> vertical lying at rows r+1, r+2
                if r + 2 < n:
                    if grid[(r + 1) * m + c] and grid[(r + 2) * m + c]:
                        nxt = base_v + (r + 1) * m + c
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll west -> horizontal lying at columns c-2, c-1
                if c >= 2:
                    if grid[row_base + c - 1] and grid[row_base + c - 2]:
                        nxt = base_h + r * h_row_len + (c - 2)
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll east -> horizontal lying at columns c+1, c+2
                if c + 2 < m:
                    if grid[row_base + c + 1] and grid[row_base + c + 2]:
                        nxt = base_h + r * h_row_len + (c + 1)
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

            elif cur < base_v:
                # Lying horizontally: covers (r,c), (r,c+1)
                hid = cur - base_h
                r = hid // h_row_len
                c = hid - r * h_row_len
                row_base = r * m

                # Roll west -> standing at c-1
                if c > 0:
                    nc = c - 1
                    if grid[row_base + nc]:
                        nxt = row_base + nc
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll east -> standing at c+2
                if c + 2 < m:
                    nc = c + 2
                    if grid[row_base + nc]:
                        nxt = row_base + nc
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll north -> same horizontal orientation one row above
                if r > 0:
                    nr = r - 1
                    nr_base = nr * m
                    if grid[nr_base + c] and grid[nr_base + c + 1]:
                        nxt = base_h + nr * h_row_len + c
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll south -> same horizontal orientation one row below
                if r + 1 < n:
                    nr = r + 1
                    nr_base = nr * m
                    if grid[nr_base + c] and grid[nr_base + c + 1]:
                        nxt = base_h + nr * h_row_len + c
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

            else:
                # Lying vertically: covers (r,c), (r+1,c)
                vid = cur - base_v
                r = vid // m
                c = vid - r * m
                row_base = r * m

                # Roll north -> standing at r-1
                if r > 0:
                    nr = r - 1
                    if grid[nr * m + c]:
                        nxt = nr * m + c
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll south -> standing at r+2
                if r + 2 < n:
                    nr = r + 2
                    if grid[nr * m + c]:
                        nxt = nr * m + c
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll west -> same vertical orientation one column left
                if c > 0:
                    nc = c - 1
                    if grid[row_base + nc] and grid[(r + 1) * m + nc]:
                        nxt = base_v + r * m + nc
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

                # Roll east -> same vertical orientation one column right
                if c + 1 < m:
                    nc = c + 1
                    if grid[row_base + nc] and grid[(r + 1) * m + nc]:
                        nxt = base_v + r * m + nc
                        if dist[nxt] == -1:
                            dist[nxt] = nd
                            append(nxt)

        for r in range(n):
            base = r * m
            answer_lines.append(
                ' '.join(str(dist[base + c]) for c in range(m))
            )

    sys.stdout.write('\n'.join(answer_lines))


if __name__ == "__main__":
    solve()