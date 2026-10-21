import sys
from array import array


def solve():
    inp = sys.stdin.buffer
    first = inp.readline()
    if not first:
        return

    T = int(first)
    output_parts = []

    for _ in range(T):
        N, M = map(int, inp.readline().split())
        x, y = map(int, inp.readline().split())

        grid = [b''.join(inp.readline().split()) for _ in range(N)]

        size_s = N * M
        size_r = N * (M - 1) if M >= 2 else 0
        size_d = (N - 1) * M if N >= 2 else 0

        r_base = size_s
        d_base = size_s + size_r
        total_states = size_s + size_r + size_d

        dist = array('i', [-1]) * total_states

        start = (x - 1) * M + (y - 1)
        dist[start] = 0

        q = array('I', [start])
        append = q.append
        head = 0

        g = grid
        dis = dist
        n = N
        m = M
        s_size = size_s
        R = r_base
        D = d_base

        while head < len(q):
            state = q[head]
            head += 1
            nd = dis[state] + 1

            if state < s_size:
                # Standing: base is one cell (r, c)
                r = state // m
                c = state - r * m

                # Roll east: covers (r, c+1), (r, c+2)
                if c + 2 < m and g[r][c + 1] == 49 and g[r][c + 2] == 49:
                    ns = R + r * (m - 1) + (c + 1)
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll west: covers (r, c-2), (r, c-1)
                if c >= 2 and g[r][c - 2] == 49 and g[r][c - 1] == 49:
                    ns = R + r * (m - 1) + (c - 2)
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll south: covers (r+1, c), (r+2, c)
                if r + 2 < n and g[r + 1][c] == 49 and g[r + 2][c] == 49:
                    ns = D + (r + 1) * m + c
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll north: covers (r-2, c), (r-1, c)
                if r >= 2 and g[r - 2][c] == 49 and g[r - 1][c] == 49:
                    ns = D + (r - 2) * m + c
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

            elif state < D:
                # Lying horizontally: covers (r, c), (r, c+1)
                local = state - R
                width = m - 1
                r = local // width
                c = local - r * width

                # Roll east -> standing at (r, c+2)
                if c + 2 < m and g[r][c + 2] == 49:
                    ns = r * m + (c + 2)
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll west -> standing at (r, c-1)
                if c >= 1 and g[r][c - 1] == 49:
                    ns = r * m + (c - 1)
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll north -> horizontal at row r-1
                if r > 0 and g[r - 1][c] == 49 and g[r - 1][c + 1] == 49:
                    ns = R + (r - 1) * width + c
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll south -> horizontal at row r+1
                if r + 1 < n and g[r + 1][c] == 49 and g[r + 1][c + 1] == 49:
                    ns = R + (r + 1) * width + c
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

            else:
                # Lying vertically: covers (r, c), (r+1, c)
                local = state - D
                r = local // m
                c = local - r * m

                # Roll south -> standing at (r+2, c)
                if r + 2 < n and g[r + 2][c] == 49:
                    ns = (r + 2) * m + c
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll north -> standing at (r-1, c)
                if r >= 1 and g[r - 1][c] == 49:
                    ns = (r - 1) * m + c
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll east -> vertical at column c+1
                if c + 1 < m and g[r][c + 1] == 49 and g[r + 1][c + 1] == 49:
                    ns = D + r * m + (c + 1)
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

                # Roll west -> vertical at column c-1
                if c > 0 and g[r][c - 1] == 49 and g[r + 1][c - 1] == 49:
                    ns = D + r * m + (c - 1)
                    if dis[ns] == -1:
                        dis[ns] = nd
                        append(ns)

        lines = []
        for r in range(n):
            base = r * m
            lines.append(' '.join(str(dis[base + c]) for c in range(m)))
        output_parts.append('\n'.join(lines))

    sys.stdout.write('\n'.join(output_parts))


if __name__ == "__main__":
    solve()