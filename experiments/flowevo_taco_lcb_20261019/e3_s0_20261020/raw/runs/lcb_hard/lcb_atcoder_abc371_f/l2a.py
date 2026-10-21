import sys


def main():
    it = iter(map(int, sys.stdin.buffer.read().split()))

    N = next(it)
    X = [next(it) for _ in range(N)]

    # z_i = position_i - i (1-indexed i)
    z = [X[i] - (i + 1) for i in range(N)]

    S = 1
    LOG = 0
    while S < N:
        S <<= 1
        LOG += 1

    M = 2 * S
    INF = 10**18
    NONE = 10**30

    seg_sum = [0] * M
    seg_min = [INF] * M
    seg_max = [-INF] * M
    seg_len = [0] * M
    lazy = [NONE] * S

    for i in range(S):
        val = z[i] if i < N else INF
        idx = S + i
        seg_sum[idx] = val
        seg_min[idx] = val
        seg_max[idx] = val
        seg_len[idx] = 1

    for i in range(S - 1, 0, -1):
        lc = i << 1
        rc = lc | 1
        seg_sum[i] = seg_sum[lc] + seg_sum[rc]
        seg_min[i] = min(seg_min[lc], seg_min[rc])
        seg_max[i] = max(seg_max[lc], seg_max[rc])
        seg_len[i] = seg_len[lc] + seg_len[rc]

    def push(k):
        v = lazy[k]
        if v != NONE:
            lc = k << 1
            rc = lc | 1

            seg_sum[lc] = v * seg_len[lc]
            seg_min[lc] = v
            seg_max[lc] = v
            if lc < S:
                lazy[lc] = v

            seg_sum[rc] = v * seg_len[rc]
            seg_min[rc] = v
            seg_max[rc] = v
            if rc < S:
                lazy[rc] = v

            lazy[k] = NONE

    def pull(k):
        lc = k << 1
        rc = lc | 1
        seg_sum[k] = seg_sum[lc] + seg_sum[rc]
        seg_min[k] = min(seg_min[lc], seg_min[rc])
        seg_max[k] = max(seg_max[lc], seg_max[rc])

    def range_assign(l, r, v):
        """Assign v to [l, r), returns old sum in [l, r)."""
        l += S
        r += S
        l0, r0 = l, r

        for i in range(LOG, 0, -1):
            if ((l0 >> i) << i) != l0:
                push(l0 >> i)
            if ((r0 >> i) << i) != r0:
                push((r0 - 1) >> i)

        old_sum = 0

        while l < r:
            if l & 1:
                old_sum += seg_sum[l]
                seg_sum[l] = v * seg_len[l]
                seg_min[l] = v
                seg_max[l] = v
                if l < S:
                    lazy[l] = v
                l += 1

            if r & 1:
                r -= 1
                old_sum += seg_sum[r]
                seg_sum[r] = v * seg_len[r]
                seg_min[r] = v
                seg_max[r] = v
                if r < S:
                    lazy[r] = v

            l >>= 1
            r >>= 1

        for i in range(1, LOG + 1):
            if ((l0 >> i) << i) != l0:
                pull(l0 >> i)
            if ((r0 >> i) << i) != r0:
                pull((r0 - 1) >> i)

        return old_sum

    def get(pos):
        k = pos + S
        for i in range(LOG, 0, -1):
            push(k >> i)
        return seg_min[k]

    def first_greater(value):
        if seg_max[1] <= value:
            return N

        k = 1
        while k < S:
            push(k)
            lc = k << 1
            if seg_max[lc] > value:
                k = lc
            else:
                k = lc | 1

        idx = k - S
        return idx if idx < N else N

    def last_less(value):
        if seg_min[1] >= value:
            return -1

        k = 1
        while k < S:
            push(k)
            rc = (k << 1) | 1
            if seg_min[rc] < value:
                k = rc
            else:
                k = k << 1

        return k - S

    Q = next(it)
    answer = 0

    for _ in range(Q):
        T = next(it)
        G = next(it)

        pos = T - 1
        c = G - T
        cur = get(pos)

        if c > cur:
            r = last_less(c)
            count = r - pos + 1
            old_sum = range_assign(pos, r + 1, c)
            answer += c * count - old_sum

        elif c < cur:
            l = first_greater(c)
            count = pos - l + 1
            old_sum = range_assign(l, pos + 1, c)
            answer += old_sum - c * count

    print(answer)


if __name__ == "__main__":
    main()