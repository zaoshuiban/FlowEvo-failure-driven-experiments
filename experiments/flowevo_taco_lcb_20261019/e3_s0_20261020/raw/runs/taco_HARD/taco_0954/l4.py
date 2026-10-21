import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    values = data[2:]
    a = [values[i * m:(i + 1) * m] for i in range(n)]

    # With one row, the traversal is just the row left-to-right.
    if n == 1:
        if m == 1:
            print(0)
        else:
            ans = min(abs(a[0][j] - a[0][j + 1]) for j in range(m - 1))
            print(ans)
        return

    INF = 10**18

    # same[i][j] = maximum k such that rows i and j can be adjacent
    # inside one column.
    same = [[0] * n for _ in range(n)]
    for i in range(n):
        ai = a[i]
        for j in range(i + 1, n):
            aj = a[j]
            best = INF
            for c in range(m):
                d = ai[c] - aj[c]
                if d < 0:
                    d = -d
                if d < best:
                    best = d
            same[i][j] = same[j][i] = best

    # cross[i][j] = maximum k such that row i as the last row of a column
    # can be followed by row j as the first row of the next column.
    if m >= 2:
        cross = [[0] * n for _ in range(n)]
        for i in range(n):
            ai = a[i]
            for j in range(n):
                aj = a[j]
                best = INF
                for c in range(m - 1):
                    d = ai[c] - aj[c + 1]
                    if d < 0:
                        d = -d
                    if d < best:
                        best = d
                cross[i][j] = best
    else:
        cross = None

    candidates = {0}
    for i in range(n):
        for j in range(i + 1, n):
            candidates.add(same[i][j])

    if cross is not None:
        for i in range(n):
            for j in range(n):
                candidates.add(cross[i][j])

    candidates = sorted(candidates)

    total_masks = 1 << n
    full_mask = total_masks - 1
    bit_value = [1 << i for i in range(n)]
    offset = [mask * n for mask in range(total_masks)]

    # bits_of[mask] = list of set-bit indices in mask.
    bits_of = [[] for _ in range(total_masks)]
    for mask in range(1, total_masks):
        lb = mask & -mask
        bits_of[mask] = bits_of[mask ^ lb] + [lb.bit_length() - 1]

    def feasible(k: int) -> bool:
        if k == 0:
            return True

        prev_allowed = [0] * n
        for last in range(n):
            mask = 0
            for prev in range(n):
                if prev != last and same[prev][last] >= k:
                    mask |= bit_value[prev]
            prev_allowed[last] = mask

        if m == 1:
            trans_allowed = [full_mask] * n
        else:
            trans_allowed = [0] * n
            for last in range(n):
                mask = 0
                row = cross[last]
                for start in range(n):
                    if row[start] >= k:
                        mask |= bit_value[start]
                trans_allowed[last] = mask

        # dp[mask, last] is a bitmask of all possible starting rows
        # for a Hamiltonian path using exactly rows in mask and ending at last.
        dp = [0] * (total_masks * n)

        for mask in range(1, total_masks):
            base = offset[mask]
            for last in bits_of[mask]:
                last_bit = bit_value[last]

                if mask == last_bit:
                    dp[base + last] = last_bit
                    continue

                prev_mask = mask ^ last_bit
                allowed = prev_allowed[last] & prev_mask
                prev_base = offset[prev_mask]

                starts = 0
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