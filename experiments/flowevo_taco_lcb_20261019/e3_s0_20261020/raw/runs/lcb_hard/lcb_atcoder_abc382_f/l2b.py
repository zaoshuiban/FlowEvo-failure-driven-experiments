import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    H = next(it)
    W = next(it)
    N = next(it)

    bars = []
    for idx in range(N):
        R = next(it)
        C = next(it) - 1
        L = next(it)
        bars.append((R, C, L, idx))

    bars.sort(reverse=True)

    ans = [0] * N
    INF = H + 1

    size = 1
    log = 0
    while size < W:
        size <<= 1
        log += 1

    seg = [INF] * (2 * size)
    lazy = [-1] * size

    def push(k):
        v = lazy[k]
        if v != -1:
            lc = k << 1
            rc = lc | 1

            seg[lc] = v
            if lc < size:
                lazy[lc] = v

            seg[rc] = v
            if rc < size:
                lazy[rc] = v

            lazy[k] = -1

    def range_min(l, r):
        l += size
        r += size
        l0, r0 = l, r

        for i in range(log, 0, -1):
            if ((l0 >> i) << i) != l0:
                push(l0 >> i)
            if ((r0 >> i) << i) != r0:
                push((r0 - 1) >> i)

        left_min = INF
        right_min = INF

        while l < r:
            if l & 1:
                if seg[l] < left_min:
                    left_min = seg[l]
                l += 1
            if r & 1:
                r -= 1
                if seg[r] < right_min:
                    right_min = seg[r]
            l >>= 1
            r >>= 1

        return left_min if left_min < right_min else right_min

    def range_assign(l, r, value):
        l += size
        r += size
        l0, r0 = l, r

        for i in range(log, 0, -1):
            if ((l0 >> i) << i) != l0:
                push(l0 >> i)
            if ((r0 >> i) << i) != r0:
                push((r0 - 1) >> i)

        while l < r:
            if l & 1:
                seg[l] = value
                if l < size:
                    lazy[l] = value
                l += 1

            if r & 1:
                r -= 1
                seg[r] = value
                if r < size:
                    lazy[r] = value

            l >>= 1
            r >>= 1

        l, r = l0, r0

        for i in range(1, log + 1):
            if ((l >> i) << i) != l:
                k = l >> i
                a = seg[k << 1]
                b = seg[k << 1 | 1]
                seg[k] = a if a < b else b

            if ((r >> i) << i) != r:
                k = (r - 1) >> i
                a = seg[k << 1]
                b = seg[k << 1 | 1]
                seg[k] = a if a < b else b

    for R, C, L, idx in bars:
        right = C + L
        highest_obstacle = range_min(C, right)
        final_row = highest_obstacle - 1

        ans[idx] = final_row
        range_assign(C, right, final_row)

    sys.stdout.write("\n".join(map(str, ans)))


if __name__ == "__main__":
    main()