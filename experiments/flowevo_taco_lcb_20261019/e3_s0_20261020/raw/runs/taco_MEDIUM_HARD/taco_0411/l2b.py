import sys
from functools import lru_cache

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    idx = 1
    out = []
    BITS = 61

    for _ in range(n):
        L = data[idx]
        R = data[idx + 1]
        idx += 2

        @lru_cache(maxsize=None)
        def dp(pos, tight_l, tight_r):
            if pos < 0:
                return 0

            lbit = (L >> pos) & 1
            rbit = (R >> pos) & 1

            lo = lbit if tight_l else 0
            hi = rbit if tight_r else 1

            best = -1
            for bit in range(lo, hi + 1):
                ntight_l = tight_l and (bit == lbit)
                ntight_r = tight_r and (bit == rbit)
                best = max(best, bit + dp(pos - 1, ntight_l, ntight_r))

            return best

        max_ones = dp(BITS - 1, True, True)

        ans = 0
        rem = max_ones
        tight_l = tight_r = True

        for pos in range(BITS - 1, -1, -1):
            lbit = (L >> pos) & 1
            rbit = (R >> pos) & 1

            lo = lbit if tight_l else 0
            hi = rbit if tight_r else 1

            for bit in (0, 1):
                if bit < lo or bit > hi:
                    continue

                ntight_l = tight_l and (bit == lbit)
                ntight_r = tight_r and (bit == rbit)

                value = bit + dp(pos - 1, ntight_l, ntight_r)

                if value == rem:
                    ans |= bit << pos
                    rem -= bit
                    tight_l, tight_r = ntight_l, ntight_r
                    break

        out.append(str(ans))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()