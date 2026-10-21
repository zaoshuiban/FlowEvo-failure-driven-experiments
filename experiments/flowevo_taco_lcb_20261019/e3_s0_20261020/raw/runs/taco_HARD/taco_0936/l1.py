import sys
import math


def possible_counts(a):
    if a == 0:
        return (0, 1)

    d = 1 + 8 * a
    r = math.isqrt(d)

    if r * r != d:
        return ()

    n = (1 + r) // 2
    if n * (n - 1) // 2 == a:
        return (n,)

    return ()


def build_string(n0, n1, a01):
    if n0 == 0:
        return '1' * n1
    if n1 == 0:
        return '0' * n0

    q, rem = divmod(a01, n1)

    parts = []

    if q > 0:
        parts.append('0' * q)

    first_ones = n1 - rem
    if first_ones > 0:
        parts.append('1' * first_ones)

    if rem > 0:
        parts.append('0')
        parts.append('1' * rem)
        trailing_zeros = n0 - q - 1
    else:
        trailing_zeros = n0 - q

    if trailing_zeros > 0:
        parts.append('0' * trailing_zeros)

    return ''.join(parts)


def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    a00, a01, a10, a11 = map(int, data[:4])

    zero_counts = possible_counts(a00)
    one_counts = possible_counts(a11)

    for n0 in zero_counts:
        for n1 in one_counts:
            if n0 + n1 == 0:
                continue

            total_cross = n0 * n1

            if a01 + a10 != total_cross:
                continue

            if a01 > total_cross:
                continue

            ans = build_string(n0, n1, a01)

            if 0 < len(ans) <= 1_000_000:
                print(ans)
                return

    print("Impossible")


if __name__ == "__main__":
    solve()