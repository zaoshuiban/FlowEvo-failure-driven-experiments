import sys
import math


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])

    # r_k = 2^k mod n
    # Expected value = sum_{k >= 0} r_k / 2^k
    r = 1 % n
    seen = {}
    values = []

    while r not in seen:
        seen[r] = len(values)
        values.append(r)
        r = (r * 2) % n

    start = seen[r]
    period_len = len(values) - start
    q = (1 << period_len) - 1

    prefix_num = 0
    for k in range(start):
        prefix_num += values[k] << (start - k)

    period_num = 0
    for t in range(period_len):
        period_num += values[start + t] << (period_len - t)

    numerator = prefix_num * q + period_num
    denominator = (1 << start) * q

    g = math.gcd(numerator, denominator)
    numerator //= g
    denominator //= g

    print(f"{numerator}/{denominator}")


if __name__ == "__main__":
    solve()