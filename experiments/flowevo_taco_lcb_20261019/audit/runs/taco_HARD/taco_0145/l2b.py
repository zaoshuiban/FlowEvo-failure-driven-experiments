import sys
import math


def solve() -> None:
    data = sys.stdin.readline().strip()
    if not data:
        return

    n = int(data)

    if n == 1:
        print("0/1")
        return

    # r_0 = 1, r_{k+1} = (2 * r_k) mod n
    # Expected number of tosses = sum_{k=0}^{inf} r_k / 2^k
    seen = [-1] * n
    values = []

    r = 1
    seen[r] = 0
    values.append(r)

    while True:
        r = (r * 2) % n

        if seen[r] != -1:
            start = seen[r]
            period_len = len(values) - start
            break

        seen[r] = len(values)
        values.append(r)

    # Prefix: sum_{k=0}^{start-1} values[k] / 2^k
    prefix_num = 0
    for pos, val in enumerate(values[:start]):
        prefix_num += val << (start - pos)

    # Period: values[start : start + period_len]
    q = (1 << period_len) - 1
    period_num = 0

    for t, val in enumerate(values[start:start + period_len]):
        period_num += val << (period_len - t)

    numerator = prefix_num * q + period_num
    denominator = (1 << start) * q

    g = math.gcd(numerator, denominator)
    numerator //= g
    denominator //= g

    print(f"{numerator}/{denominator}")


if __name__ == "__main__":
    solve()