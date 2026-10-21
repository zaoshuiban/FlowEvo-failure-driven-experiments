import sys
from math import isqrt


def possible_lengths(tri):
    """
    Returns all n >= 0 such that n * (n - 1) / 2 == tri.
    For tri == 0, both n = 0 and n = 1 are possible.
    """
    if tri == 0:
        return (0, 1)

    d = 1 + 8 * tri
    r = isqrt(d)

    if r * r != d:
        return ()

    n = (1 + r) // 2
    if n * (n - 1) // 2 == tri:
        return (n,)

    return ()


def build_string(n0, n1, a01):
    """
    Builds a binary string with n0 zeros and n1 ones
    such that the number of '01' subsequences is a01.
    """
    if n1 == 0:
        return '0' * n0

    if n0 == 0:
        return '1' * n1

    q, r = divmod(a01, n1)

    if q > n0:
        return None
    if r and q + 1 > n0:
        return None

    # gaps[i] = number of ones placed after exactly i zeros
    gaps = [0] * (n0 + 1)
    gaps[q] += n1 - r
    if r:
        gaps[q + 1] += r

    parts = []
    for i in range(n0 + 1):
        if gaps[i]:
            parts.append('1' * gaps[i])
        if i < n0:
            parts.append('0')

    return ''.join(parts)


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if len(data) < 4:
        return

    a00, a01, a10, a11 = data[:4]

    for n0 in possible_lengths(a00):
        for n1 in possible_lengths(a11):
            if n0 + n1 == 0:
                continue

            if n0 * n1 != a01 + a10:
                continue

            if n0 + n1 > 1_000_000:
                continue

            s = build_string(n0, n1, a01)
            if s is not None:
                sys.stdout.write(s + '\n')
                return

    sys.stdout.write("Impossible\n")


if __name__ == "__main__":
    solve()