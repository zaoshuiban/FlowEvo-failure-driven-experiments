import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    a = [[next(it) for _ in range(m)] for _ in range(n)]
    INF = 10**18

    if n == 1:
        if m == 1:
            print(0)
            return
        row = a[0]
        ans = INF
        for c in range(m - 1):
            diff = row[c] - row[c + 1]
            if diff < 0:
                diff = -diff
            if diff < ans:
                ans = diff
        print(ans)
        return

    # w[i][j] = minimum possible absolute difference between rows i and j
    # inside the same column.
    w = [[0] * n for _ in range(n)]
    for i in range(n):
        ai = a[i]
        for j in range(i + 1, n):
            aj = a[j]
            mn = INF
            for c in range(m):
                diff = ai[c] - aj[c]
                if diff < 0:
                    diff = -diff
                if diff < mn:
                    mn = diff
                    if mn == 0:
                        break
            w[i][j] = mn
            w[j][i] = mn

    # d[end][start] = minimum absolute difference between the last row
    # of one column and the first row of the next column.
    d = [[INF] * n for _ in range(n)]
    if m > 1:
        for i in range(n):
            ai = a[i]
            di = d[i]
            for j in range(n):
                aj = a[j]
                mn = INF
                for c in range(m - 1):
                    diff = ai[c] - aj[c + 1]
                    if diff < 0:
                        diff = -diff
                    if diff < mn:
                        mn = diff
                        if mn == 0:
                            break
                di[j] = mn

    size = 1 << n
    total = size * n

    base = [mask * n for mask in range(size)]

    bits = [None] * size
    bits[0] = []
    for mask in range(1, size):
        lb = mask & -mask
        bits[mask] = bits[mask ^ lb] + [lb.bit_length() - 1]

    one = [1 << i for i in range(n)]
    full = size - 1
    fullbase = base[full]

    ans = 0

    # Fix the first row s. Since the internal bottleneck is symmetric,
    # it is enough to consider endpoints e > s and take the better
    # orientation for the column-boundary condition.
    for s in range(n - 1):
        dp = [-1] * total
        bit_s = one[s]
        dp[base[bit_s] + s] = INF

        for mask in range(size):
            if (mask & bit_s) == 0 or mask == bit_s:
                continue

            mask_base = base[mask]
            others = mask ^ bit_s

            for last in bits[others]:
                prevmask = mask ^ one[last]
                prev_base = base[prevmask]

                if prevmask == bit_s:
                    dp[mask_base + last] = w[s][last]
                else:
                    best = -1
                    w_last = w[last]
                    prev_others = prevmask ^ bit_s

                    for prev in bits[prev_others]:
                        val = dp[prev_base + prev]
                        edge = w_last[prev]

                        if edge < val:
                            cand = edge
                        else:
                            cand = val

                        if cand > best:
                            best = cand

                    dp[mask_base + last] = best

        for e in range(s + 1, n):
            val = dp[fullbase + e]
            if val >= 0:
                b1 = d[e][s]
                b2 = d[s][e]
                boundary = b1 if b1 > b2 else b2

                cand = val if val < boundary else boundary
                if cand > ans:
                    ans = cand

    print(ans)


if __name__ == "__main__":
    solve()