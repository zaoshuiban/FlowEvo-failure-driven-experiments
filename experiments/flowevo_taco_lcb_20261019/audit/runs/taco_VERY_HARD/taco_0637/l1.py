import sys
from array import array


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    ptr = 0
    T = int(data[ptr])
    ptr += 1
    out = []

    for _ in range(T):
        N = int(data[ptr])
        M = int(data[ptr + 1])
        ptr += 2

        x = int(data[ptr]) - 1
        y = int(data[ptr + 1]) - 1
        ptr += 2

        free = bytearray(N * M)

        for r in range(N):
            token = data[ptr]
            ptr += 1

            if len(token) != M:
                row = token
                while len(row) < M:
                    row += data[ptr]
                    ptr += 1
            else:
                row = token

            off = r * M
            for c in range(M):
                if row[c] == 49:  # ord('1')
                    free[off + c] = 1

        S_count = N * M
        H_width = M - 1
        H_count = N * H_width if H_width > 0 else 0
        V_count = (N - 1) * M if N > 1 else 0

        total = S_count + H_count + V_count
        dist = array('i', [-1]) * total

        start = x * M + y
        dist[start] = 0

        queue = array('i', [start])
        head = 0

        H_off = S_count
        V_off = S_count + H_count

        fr = free
        ds = dist
        append = queue.append

        while head < len(queue):
            cur = queue[head]
            head += 1

            nd = ds[cur] + 1

            if cur < S_count:
                r = cur // M
                c = cur - r * M
                rowbase = r * M

                # Roll east
                if c + 2 < M:
                    p = rowbase + c + 1
                    if fr[p] and fr[p + 1]:
                        nid = H_off + r * H_width + c + 1
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll west
                if c >= 2:
                    p = rowbase + c - 2
                    if fr[p] and fr[p + 1]:
                        nid = H_off + r * H_width + c - 2
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll south
                if r + 2 < N:
                    p = (r + 1) * M + c
                    if fr[p] and fr[p + M]:
                        nid = V_off + p
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll north
                if r >= 2:
                    p = (r - 2) * M + c
                    if fr[p] and fr[p + M]:
                        nid = V_off + p
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

            elif cur < V_off:
                t = cur - H_off
                r = t // H_width
                c = t - r * H_width
                rowbase = r * M

                # Roll east along the length
                if c + 2 < M:
                    p = rowbase + c + 2
                    if fr[p]:
                        nid = p
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll west along the length
                if c >= 1:
                    p = rowbase + c - 1
                    if fr[p]:
                        nid = p
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll north sideways
                if r > 0:
                    p = (r - 1) * M + c
                    if fr[p] and fr[p + 1]:
                        nid = H_off + (r - 1) * H_width + c
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll south sideways
                if r + 1 < N:
                    p = (r + 1) * M + c
                    if fr[p] and fr[p + 1]:
                        nid = H_off + (r + 1) * H_width + c
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

            else:
                t = cur - V_off
                r = t // M
                c = t - r * M
                rowbase = r * M

                # Roll south along the length
                if r + 2 < N:
                    p = (r + 2) * M + c
                    if fr[p]:
                        nid = p
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll north along the length
                if r >= 1:
                    p = (r - 1) * M + c
                    if fr[p]:
                        nid = p
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll east sideways
                if c + 1 < M:
                    p = rowbase + c + 1
                    if fr[p] and fr[p + M]:
                        nid = V_off + p
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

                # Roll west sideways
                if c >= 1:
                    p = rowbase + c - 1
                    if fr[p] and fr[p + M]:
                        nid = V_off + p
                        if ds[nid] == -1:
                            ds[nid] = nd
                            append(nid)

        for r in range(N):
            rowbase = r * M
            out.append(' '.join(str(ds[rowbase + c]) for c in range(M)))

    sys.stdout.write('\n'.join(out))


if __name__ == "__main__":
    solve()