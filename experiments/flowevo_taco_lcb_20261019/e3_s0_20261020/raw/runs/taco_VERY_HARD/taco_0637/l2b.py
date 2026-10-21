import sys
from array import array


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    T = int(next(it))
    out_lines = []

    for _ in range(T):
        N = int(next(it))
        M = int(next(it))
        x = int(next(it)) - 1
        y = int(next(it)) - 1

        stride = M + 5
        free = bytearray((N + 5) * stride)

        for i in range(N):
            start_idx = (i + 2) * stride + 2
            j = 0
            while j < M:
                token = next(it)
                for ch in token:
                    if j >= M:
                        break
                    if ch == 49:  # '1'
                        free[start_idx + j] = 1
                    j += 1

        # State encoding:
        # S: i * M + j
        # H: offsetH + i * (M - 1) + j, covers (i, j), (i, j + 1)
        # V: offsetV + i * M + j, covers (i, j), (i + 1, j)

        S_count = N * M
        hc = M - 1 if M > 1 else 0
        H_count = N * hc
        V_count = (N - 1) * M if N > 1 else 0

        distS = array('i', [-1]) * S_count
        visitedH = bytearray(H_count)
        visitedV = bytearray(V_count)

        start = x * M + y
        distS[start] = 0

        q = array('I', [start])
        head = 0
        level = 0

        offsetH = S_count
        offsetV = S_count + H_count

        f = free
        st = stride
        dS = distS
        vH = visitedH
        vV = visitedV
        n = N
        m = M
        hc_local = hc

        while head < len(q):
            level_end = len(q)
            next_level = level + 1

            while head < level_end:
                state = q[head]
                head += 1

                if state < S_count:
                    i = state // m
                    j = state - i * m
                    rowbase = (i + 2) * st + (j + 2)

                    # East: S -> H covering (i, j+1), (i, j+2)
                    if j + 2 < m and f[rowbase + 1] and f[rowbase + 2]:
                        hloc = i * hc_local + (j + 1)
                        if not vH[hloc]:
                            vH[hloc] = 1
                            q.append(offsetH + hloc)

                    # West: S -> H covering (i, j-2), (i, j-1)
                    if j >= 2 and f[rowbase - 1] and f[rowbase - 2]:
                        hloc = i * hc_local + (j - 2)
                        if not vH[hloc]:
                            vH[hloc] = 1
                            q.append(offsetH + hloc)

                    # South: S -> V covering (i+1, j), (i+2, j)
                    if i + 2 < n and f[rowbase + st] and f[rowbase + 2 * st]:
                        vloc = (i + 1) * m + j
                        if not vV[vloc]:
                            vV[vloc] = 1
                            q.append(offsetV + vloc)

                    # North: S -> V covering (i-2, j), (i-1, j)
                    if i >= 2 and f[rowbase - st] and f[rowbase - 2 * st]:
                        vloc = (i - 2) * m + j
                        if not vV[vloc]:
                            vV[vloc] = 1
                            q.append(offsetV + vloc)

                elif state < offsetV:
                    # H state
                    z = state - offsetH
                    i = z // hc_local
                    j = z - i * hc_local
                    rowbase = (i + 2) * st + (j + 2)

                    # Roll east over the right short edge -> standing at (i, j+2)
                    if j + 2 < m and f[rowbase + 2]:
                        idx = i * m + j + 2
                        if dS[idx] == -1:
                            dS[idx] = next_level
                            q.append(idx)

                    # Roll west over the left short edge -> standing at (i, j-1)
                    if j >= 1 and f[rowbase - 1]:
                        idx = i * m + j - 1
                        if dS[idx] == -1:
                            dS[idx] = next_level
                            q.append(idx)

                    # Roll north over a long edge -> H in row i-1
                    if i > 0 and f[rowbase - st] and f[rowbase - st + 1]:
                        hloc = (i - 1) * hc_local + j
                        if not vH[hloc]:
                            vH[hloc] = 1
                            q.append(offsetH + hloc)

                    # Roll south over a long edge -> H in row i+1
                    if i + 1 < n and f[rowbase + st] and f[rowbase + st + 1]:
                        hloc = (i + 1) * hc_local + j
                        if not vH[hloc]:
                            vH[hloc] = 1
                            q.append(offsetH + hloc)

                else:
                    # V state
                    z = state - offsetV
                    i = z // m
                    j = z - i * m
                    rowbase = (i + 2) * st + (j + 2)

                    # Roll north over the top short edge -> standing at (i-1, j)
                    if i >= 1 and f[rowbase - st]:
                        idx = (i - 1) * m + j
                        if dS[idx] == -1:
                            dS[idx] = next_level
                            q.append(idx)

                    # Roll south over the bottom short edge -> standing at (i+2, j)
                    if i + 2 < n and f[rowbase + 2 * st]:
                        idx = (i + 2) * m + j
                        if dS[idx] == -1:
                            dS[idx] = next_level
                            q.append(idx)

                    # Roll west over a long edge -> V in column j-1
                    if j > 0 and f[rowbase - 1] and f[rowbase + st - 1]:
                        vloc = i * m + j - 1
                        if not vV[vloc]:
                            vV[vloc] = 1
                            q.append(offsetV + vloc)

                    # Roll east over a long edge -> V in column j+1
                    if j + 1 < m and f[rowbase + 1] and f[rowbase + st + 1]:
                        vloc = i * m + j + 1
                        if not vV[vloc]:
                            vV[vloc] = 1
                            q.append(offsetV + vloc)

            level = next_level

        for i in range(n):
            base = i * m
            out_lines.append(
                ' '.join(str(dS[base + j]) for j in range(m))
            )

    sys.stdout.write('\n'.join(out_lines))


if __name__ == "__main__":
    solve()