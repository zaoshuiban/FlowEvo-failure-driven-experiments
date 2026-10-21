import sys
from math import isqrt


def possible_n(a):
    if a == 0:
        return (0, 1)

    d = 1 + 8 * a
    r = isqrt(d)

    if r * r != d:
        return ()

    n = (1 + r) // 2
    if n * (n - 1) // 2 == a:
        return (n,)

    return ()


def count_subsequences(s):
    zeros = ones = 0
    c00 = c01 = c10 = c11 = 0

    for ch in s:
        if ch == '0':
            c00 += zeros
            c10 += ones
            zeros += 1
        else:
            c11 += ones
            c01 += zeros
            ones += 1

    return c00, c01, c10, c11


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if len(data) < 4:
        return

    a00, a01, a10, a11 = data[:4]

    for n0 in possible_n(a00):
        for n1 in possible_n(a11):
            if n0 + n1 == 0:
                continue

            if n0 * n1 != a01 + a10:
                continue

            if n0 + n1 > 1_000_000:
                continue

            if n1 == 0:
                s = '0' * n0
            elif n0 == 0:
                s = '1' * n1
            else:
                q, r = divmod(a01, n1)

                if q > n0 or (r and q + 1 > n0):
                    continue

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

                s = ''.join(parts)

            if count_subsequences(s) == (a00, a01, a10, a11):
                sys.stdout.write(s + '\n')
                return

    sys.stdout.write("Impossible\n")


if __name__ == "__main__":
    solve()