import sys
import math


def possible_counts(a):
    if a == 0:
        return (0, 1)

    d = 1 + 8 * a
    r = math.isqrt(d)
    if r * r == d:
        n = (1 + r) // 2
        if n * (n - 1) // 2 == a:
            return (n,)

    return ()


def build_string(n0, n1, a01):
    if n1 == 0:
        return '0' * n0

    q, r = divmod(a01, n1)

    parts = []

    if q:
        parts.append('0' * q)

    first_ones = n1 - r
    if first_ones:
        parts.append('1' * first_ones)

    if r:
        parts.append('0')
        parts.append('1' * r)
        remaining_zeros = n0 - q - 1
    else:
        remaining_zeros = n0 - q

    if remaining_zeros:
        parts.append('0' * remaining_zeros)

    return ''.join(parts)


def main():
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return

    a00, a01, a10, a11 = data[:4]

    for n0 in possible_counts(a00):
        for n1 in possible_counts(a11):
            if n0 + n1 == 0:
                continue

            if n0 * (n0 - 1) // 2 != a00:
                continue
            if n1 * (n1 - 1) // 2 != a11:
                continue

            total_cross = n0 * n1

            if a01 + a10 != total_cross:
                continue

            if not (0 <= a01 <= total_cross):
                continue

            answer = build_string(n0, n1, a01)

            if len(answer) <= 1_000_000:
                print(answer)
                return

    print("Impossible")


if __name__ == "__main__":
    main()