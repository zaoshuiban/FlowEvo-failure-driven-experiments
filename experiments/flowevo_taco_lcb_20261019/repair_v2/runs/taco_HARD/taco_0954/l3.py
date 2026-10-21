import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    values = data[2:]
    a = [values[i * m:(i + 1) * m] for i in range(n)]

    # Only one row: row order does not matter.
    if n == 1:
        if m == 1:
            print(0)
        else:
            row = a[0]
            ans = min(abs(row[j] - row[j + 1]) for j in range(m - 1))
            print(ans)
        return

    INF = 10**18

    # w[i][j] = maximum k such that rows i and j can be adjacent
    # inside the same column.
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
            w[i][j] = w[j][i] = best

    # trans[i][j] = maximum k such that row i as the last row of a column
    # can be followed by row j as the first row of the next column.
    if m >= 2:
        trans = [[0] * n for _ in range(n)]
        for i in range(n):
            ri = a[i]
            row_trans = trans[i]
            for j in range(n):
                rj = a[j]
                best = INF
                for c in range(m - 1):
                    d = ri[c] - rj[c + 1]
                    if d < 0:
                        d = -d
                    if d < best:
                        best = d
                row_trans[j] = best
    else:
        trans = None

    candidates = {0}
    for i in range(n):
        for j in range(i + 1, n):
            candidates.add(w[i][j])

    if m >= 2:
        for i in range(n):
            for j in range(n):
                candidates.add(trans[i][j])

    candidates = sorted(candidates)

    total_masks = 1 << n
    full_mask = total_masks - 1

    offset = [mask * n for mask in range(total_masks)]

    # bits_of[mask] = list of set bit indices in mask.
    bits_of = [[] for _ in range(total_masks)]
    for mask in range(1, total_masks):
        lb = mask & -mask
        bits_of[mask] = bits_of[mask ^ lb] + [lb.bit_length() - 1]

    bit_values = [1 << i for i in range(n)]

    def feasible(k: int) -> bool:
        if k == 0:
            return True

        # prev_allowed[last] contains rows that can precede last.
        prev_allowed = [0] * n
        for last in range(n):
            mask = 0
            for prev in range(n):
                if prev != last and w[prev][last] >= k:
                    mask |= bit_values[prev]
            prev_allowed[last] = mask

        # trans_allowed[last] contains possible first rows after finishing at last.
        trans_allowed = [0] * n
        if m == 1:
            for last in range(n):
                trans_allowed[last] = full_mask
        else:
            for last in range(n):
                mask = 0
                row = trans[last]
                for start in range(n):
                    if row[start] >= k:
                        mask |= bit_values[start]
                trans_allowed[last] = mask

        # dp[mask, last] = bitmask of all possible starting rows
        # for a Hamiltonian path using exactly rows in mask and ending at last.
        dp = [0] * (total_masks * n)

        for mask in range(1, total_masks):
            base = offset[mask]
            for last in bits_of[mask]:
                last_bit = bit_values[last]

                if mask == last_bit:
                    dp[base + last] = last_bit
                    continue

                prev_mask = mask ^ last_bit
                allowed = prev_allowed[last] & prev_mask
                starts = 0
                prev_base = offset[prev_mask]

                for prev in bits_of[allowed]:
                    starts |= dp[prev_base + prev]

                dp[base + last] = starts

        base = offset[full_mask]
        for last in range(n):
            if dp[base + last] & trans_allowed[last]:
                return True

        return False

    left = 0
    right = len(candidates) - 1
    answer = 0

    while left <= right:
        mid = (left + right) // 2
        k = candidates[mid]

        if feasible(k):
            answer = k
            left = mid + 1
        else:
            right = mid - 1

    print(answer)


if __name__ == "__main__":
    solve()