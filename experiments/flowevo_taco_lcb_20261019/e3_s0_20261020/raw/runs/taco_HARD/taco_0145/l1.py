import sys
import math

def solve() -> None:
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])

    seen = {}
    values = []

    r = 1 % n
    while r not in seen:
        seen[r] = len(values)
        values.append(r)
        r = (r * 2) % n

    mu = seen[r]
    length = len(values) - mu

    prefix = values[:mu]
    cycle = values[mu:]

    # Prefix sum:
    # sum_{d=0}^{mu-1} values[d] / 2^d
    f = 0
    for v in prefix:
        f = (f << 1) + v
    prefix_num = f << 1  # denominator is 2^mu

    # Cycle sum numerator:
    # sum_{j=0}^{length-1} cycle[j] * 2^(length-j)
    e = 0
    for v in cycle:
        e = (e << 1) + v
    cycle_num = e << 1

    pow2_len = 1 << length

    numerator = prefix_num * (pow2_len - 1) + cycle_num
    denominator = (1 << mu) * (pow2_len - 1)

    g = math.gcd(numerator, denominator)
    numerator //= g
    denominator //= g

    print(f"{numerator}/{denominator}")


if __name__ == "__main__":
    solve()