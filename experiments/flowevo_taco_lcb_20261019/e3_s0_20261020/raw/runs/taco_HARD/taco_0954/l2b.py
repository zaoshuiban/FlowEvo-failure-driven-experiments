import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    a = [[next(it) for _ in range(m)] for _ in range(n)]

    if n == 1:
        row = a[0]
        ans = min(abs(row[j] - row[j + 1]) for j in range(m - 1))
        print(ans)
        return

    INF = 10**30

    # w[i][j] = minimum difference between rows i and j in the same column
    w = [[0] * n for _ in range(n)]
    for i in range(n):
        ri = a[i]
        for j in range(i + 1, n):
            rj = a[j]
            best = INF
            for c in range(m):
                d = ri[c] - rj[c]
                if d < 0:
                    d = -d
                if d < best:
                    best = d
            w[i][j] = best
            w[j][i] = best

    # trans[i][j] = minimum difference between row i of column c
    # and row j of column c + 1
    if m >= 2:
        trans = [[0] * n for _ in range(n)]
        for i in range(n):
            ri = a[i]
            for j in range(n):
                rj = a[j]
                best = INF
                for c in range(m - 1):
                    d = ri[c] - rj[c + 1]
                    if d < 0:
                        d = -d
                    if d < best:
                        best = d
                trans[i][j] = best
    else:
        trans = None

    candidates = {0}

    for i in range(n):
        for j in range(n):
            if i != j:
                candidates.add(w[i][j])
            if m >= 2:
                candidates.add(trans[i][j])

    values = sorted(candidates)

    total_masks = 1 << n
    full_mask = total_masks - 1
    all_bits = full_mask

    def feasible(k: int) -> bool:
        prev_allowed = [0] * n

        for last in range(n):
            mask = 0
            for prev in range(n):
                if prev != last and w[prev][last] >= k:
                    mask |= 1 << prev
            prev_allowed[last] = mask

        trans_allowed = [0] * n

        if m == 1:
            for last in range(n):
                trans_allowed[last] = all_bits
        else:
            for last in range(n):
                mask = 0
                row = trans[last]
                for start in range(n):
                    if row[start] >= k:
                        mask |= 1 << start
                trans_allowed[last] = mask

        dp = [0] * (total_masks * n)

        for mask in range(1, total_masks):
            base = mask * n
            bits = mask

            while bits:
                lb = bits & -bits
                last = lb.bit_length() - 1

                if mask == lb:
                    dp[base + last] = lb
                else:
                    prev_mask = mask ^ lb
                    prev_base = prev_mask * n

                    allowed = prev_allowed[last] & prev_mask
                    starts = 0

                    while allowed:
                        plb = allowed & -allowed
                        prev = plb.bit_length() - 1
                        starts |= dp[prev_base + prev]
                        allowed -= plb

                    dp[base + last] = starts

                bits -= lb

        base = full_mask * n

        for last in range(n):
            if dp[base + last] & trans_allowed[last]:
                return True

        return False

    left = 0
    right = len(values) - 1
    answer = 0

    while left <= right:
        mid = (left + right) // 2
        k = values[mid]

        if feasible(k):
            answer = k
            left = mid + 1
        else:
            right = mid - 1

    print(answer)


if __name__ == "__main__":
    solve()