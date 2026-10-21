import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    H, W, Q = data[0], data[1], data[2]

    N = H * W
    active = bytearray([1]) * N

    row_next = list(range(N))
    row_prev = list(range(N))
    col_next = list(range(N))
    col_prev = list(range(N))

    def find(par, x):
        if x == -1:
            return -1

        r = x
        while par[r] != r:
            r = par[r]
            if r == -1:
                while x != -1 and par[x] != x:
                    nxt = par[x]
                    par[x] = -1
                    x = nxt
                return -1

        while x != r:
            nxt = par[x]
            par[x] = r
            x = nxt

        return r

    def erase(idx):
        if active[idx] == 0:
            return 0

        active[idx] = 0
        r = idx // W
        c = idx % W

        if c + 1 < W:
            row_next[idx] = find(row_next, idx + 1)
        else:
            row_next[idx] = -1

        if c > 0:
            row_prev[idx] = find(row_prev, idx - 1)
        else:
            row_prev[idx] = -1

        if r + 1 < H:
            col_next[idx] = find(col_next, idx + W)
        else:
            col_next[idx] = -1

        if r > 0:
            col_prev[idx] = find(col_prev, idx - W)
        else:
            col_prev[idx] = -1

        return 1

    walls = N
    p = 3

    for _ in range(Q):
        R = data[p] - 1
        C = data[p + 1] - 1
        p += 2

        idx = R * W + C

        if active[idx]:
            walls -= erase(idx)
        else:
            candidates = []

            if C > 0:
                x = find(row_prev, idx - 1)
                if x != -1:
                    candidates.append(x)

            if C + 1 < W:
                x = find(row_next, idx + 1)
                if x != -1:
                    candidates.append(x)

            if R > 0:
                x = find(col_prev, idx - W)
                if x != -1:
                    candidates.append(x)

            if R + 1 < H:
                x = find(col_next, idx + W)
                if x != -1:
                    candidates.append(x)

            for x in candidates:
                walls -= erase(x)

    print(walls)


if __name__ == "__main__":
    solve()