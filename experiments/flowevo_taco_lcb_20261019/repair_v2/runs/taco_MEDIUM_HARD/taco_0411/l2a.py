import sys
from functools import lru_cache

MAX_BIT = 60

def solve_query(l, r):
    @lru_cache(maxsize=None)
    def dp(pos, tight_low, tight_high):
        if pos < 0:
            return 0

        low_bit = (l >> pos) & 1
        high_bit = (r >> pos) & 1
        best = -1

        for bit in (0, 1):
            if tight_low and bit < low_bit:
                continue
            if tight_high and bit > high_bit:
                continue

            next_tight_low = tight_low and (bit == low_bit)
            next_tight_high = tight_high and (bit == high_bit)

            best = max(
                best,
                bit + dp(pos - 1, next_tight_low, next_tight_high)
            )

        return best

    remaining = dp(MAX_BIT, True, True)

    answer = 0
    tight_low = True
    tight_high = True

    for pos in range(MAX_BIT, -1, -1):
        low_bit = (l >> pos) & 1
        high_bit = (r >> pos) & 1

        for bit in (0, 1):
            if tight_low and bit < low_bit:
                continue
            if tight_high and bit > high_bit:
                continue

            next_tight_low = tight_low and (bit == low_bit)
            next_tight_high = tight_high and (bit == high_bit)

            current = bit + dp(pos - 1, next_tight_low, next_tight_high)

            if current == remaining:
                if bit:
                    answer |= 1 << pos

                remaining -= bit
                tight_low = next_tight_low
                tight_high = next_tight_high
                break

    return answer


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    results = []
    idx = 1

    for _ in range(n):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        results.append(str(solve_query(l, r)))

    sys.stdout.write("\n".join(results))


if __name__ == "__main__":
    main()