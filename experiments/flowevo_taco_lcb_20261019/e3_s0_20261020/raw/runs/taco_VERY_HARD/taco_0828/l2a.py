import sys
from collections import deque


def solve():
    tokens = sys.stdin.buffer.read().split()
    if not tokens:
        return

    t = int(tokens[0])
    idx = 1
    out = []

    DOT = ord('.')
    INF = 10**9

    for _ in range(t):
        n = int(tokens[idx])
        m = int(tokens[idx + 1])
        idx += 2

        grid = tokens[idx:idx + n]
        idx += n

        total_cells = n * m
        row_offset = total_cells
        total_nodes = total_cells + n

        dist = [INF] * total_nodes
        visited = bytearray(total_nodes)

        dq = deque()
        dist[0] = 0
        dq.append(0)

        last_row = n - 1
        if grid[last_row][m - 1] == DOT:
            target = total_cells - 1
        else:
            target = row_offset + last_row

        while dq:
            v = dq.popleft()

            if visited[v]:
                continue
            visited[v] = 1

            d = dist[v]

            if v == target:
                break

            if v < total_cells:
                row = v // m
                col = v - row * m

                if row > 0:
                    nid = v - m
                    if grid[row - 1][col] == DOT and d < dist[nid]:
                        dist[nid] = d
                        dq.appendleft(nid)

                if row + 1 < n:
                    nid = v + m
                    if grid[row + 1][col] == DOT and d < dist[nid]:
                        dist[nid] = d
                        dq.appendleft(nid)

                if col > 0:
                    nid = v - 1
                    if grid[row][col - 1] == DOT and d < dist[nid]:
                        dist[nid] = d
                        dq.appendleft(nid)

                if col + 1 < m:
                    nid = v + 1
                    if grid[row][col + 1] == DOT and d < dist[nid]:
                        dist[nid] = d
                        dq.appendleft(nid)

                nd = d + 1

                rv = row_offset + row
                if nd < dist[rv]:
                    dist[rv] = nd
                    dq.append(rv)

                if row > 0:
                    rv = row_offset + row - 1
                    if nd < dist[rv]:
                        dist[rv] = nd
                        dq.append(rv)

                if row + 1 < n:
                    rv = row_offset + row + 1
                    if nd < dist[rv]:
                        dist[rv] = nd
                        dq.append(rv)

            else:
                row = v - row_offset

                if row > 0:
                    s = row - 1
                    base = s * m
                    row_bytes = grid[s]

                    for col in range(m):
                        if row_bytes[col] == DOT:
                            nid = base + col
                            if d < dist[nid]:
                                dist[nid] = d
                                dq.appendleft(nid)

                s = row
                base = s * m
                row_bytes = grid[s]

                for col in range(m):
                    if row_bytes[col] == DOT:
                        nid = base + col
                        if d < dist[nid]:
                            dist[nid] = d
                            dq.appendleft(nid)

                if row + 1 < n:
                    s = row + 1
                    base = s * m
                    row_bytes = grid[s]

                    for col in range(m):
                        if row_bytes[col] == DOT:
                            nid = base + col
                            if d < dist[nid]:
                                dist[nid] = d
                                dq.appendleft(nid)

                nd = d + 1

                if row > 0:
                    rv = row_offset + row - 1
                    if nd < dist[rv]:
                        dist[rv] = nd
                        dq.append(rv)

                if row + 1 < n:
                    rv = row_offset + row + 1
                    if nd < dist[rv]:
                        dist[rv] = nd
                        dq.append(rv)

        out.append(str(dist[target]))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()