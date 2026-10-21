import sys
from math import isqrt


def possible_counts(a):
    if a == 0:
        return (0, 1)

    d = 1 + 8 * a
    r = isqrt(d)

    if r * r != d:
        return ()

    if (1 + r) % 2 != 0:
        return ()

    n = (1 + r) // 2

    if n * (n - 1) // 2 == a:
        return (n,)

    return ()


def solve():
    a00, a01, a10, a11 = map(int, sys.stdin.buffer.readline().split())

    zero_counts = possible_counts(a00)
    one_counts = possible_counts(a11)

    for n0 in zero_counts:
        for n1 in one_counts:
            if n0 + n1 == 0:
                continue

            if a01 + a10 != n0 * n1:
                continue

            if n1 == 0:
                result = "0" * n0
            elif n0 == 0:
                result = "1" * n1
            else:
                gaps = [0] * (n0 + 1)

                q, r = divmod(a01, n1)

                if q > n0:
                    continue

                gaps[q] += n1 - r

                if r:
                    if q + 1 > n0:
                        continue
                    gaps[q + 1] += r

                parts = []

                for i in range(n0 + 1):
                    if gaps[i]:
                        parts.append("1" * gaps[i])
                    if i < n0:
                        parts.append("0")

                result = "".join(parts)

            if result and len(result) <= 1_000_000:
                print(result)
                return

    print("Impossible")


if __name__ == "__main__":
    solve()