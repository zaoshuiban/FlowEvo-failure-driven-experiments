import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    a = [[next(it) for _ in range(m)] for _ in range(n)]

    INF = 10**18

    # w[i][j] = minimum difference between rows i and j in the same column
    w = [[0] * n for _ in range(n)]
    for i in range(n):
        wi = w[i]
        ai = a[i]
        for j in range(i + 1, n):
            aj = a[j]
            mn = INF
            for c in range(m):
                d = ai[c] - aj[c]
                if d < 0:
                    d = -d
                if d < mn:
                    mn = d
            wi[j] = mn
            w[j][i] = mn

    # b[first][last] = minimum difference between:
    # last row in column c and first row in column c + 1
    b = [[INF] * n for _ in range(n)]
    if m > 1:
        for first in range(n):
            af = a[first]
            bf = b[first]
            for last in range(n):
                al = a[last]
                mn = INF
                for c in range(m - 1):
                    d = al[c] - af[c + 1]
                    if d < 0:
                        d = -d
                    if d < mn:
                        mn = d
                bf[last] = mn

    candidates = {0}
    for i in range(n):
        for j in range(i + 1, n):
            candidates.add(w[i][j])

    if m > 1:
        for first in range(n):
            for last in range(n):
                candidates.add(b[first][last])

    candidates = sorted(candidates)

    full = 1 << n
    allmask = full - 1
    base_of_mask = [mask * n for mask in range(full)]

    bit_pos = [0] * full
    for i in range(n):
        bit_pos[1 << i] = i

    def feasible(k: int) -> bool:
        adj = [0] * n
        for i in range(n):
            wi = w[i]
            mask = 0
            for j in range(n):
                if i != j and wi[j] >= k:
                    mask |= 1 << j
            adj[i] = mask

        good = [0] * n
        for first in range(n):
            bit = 1 << first
            bf = b[first]
            for last in range(n):
                if bf[last] >= k:
                    good[last] |= bit

        dp = [0] * (full * n)

        for v in range(n):
            dp[base_of_mask[1 << v] + v] = 1 << v

        for mask in range(1, allmask):
            base = base_of_mask[mask]
            remaining = allmask ^ mask
            bits = mask

            while bits:
                lb = bits & -bits
                last = bit_pos[lb]
                firsts = dp[base + last]

                if firsts:
                    can = adj[last] & remaining
                    while can:
                        ub = can & -can
                        nxt = bit_pos[ub]
                        new_mask = mask | ub
                        idx = base_of_mask[new_mask] + nxt
                        dp[idx] |= firsts
                        can ^= ub

                bits ^= lb

        full_base = base_of_mask[allmask]
        for last in range(n):
            if dp[full_base + last] & good[last]:
                return True

        return False

    lo = 0
    hi = len(candidates) - 1

    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(candidates[mid]):
            lo = mid
        else:
            hi = mid - 1

    print(candidates[lo])


if __name__ == "__main__":
    main()