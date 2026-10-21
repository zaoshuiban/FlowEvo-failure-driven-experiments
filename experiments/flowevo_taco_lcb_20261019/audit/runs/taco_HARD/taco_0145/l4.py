import sys
import math


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])

    # Avoid possible integer-to-string conversion limit on newer Python versions.
    if hasattr(sys, "set_int_max_str_digits"):
        sys.set_int_max_str_digits(0)

    # r_k = 2^k mod n.
    # The sequence is eventually periodic.
    first = [-1] * n
    seq = []

    r = 1 % n
    while first[r] == -1:
        first[r] = len(seq)
        seq.append(r)
        r = (r * 2) % n

    start = first[r]
    period_len = len(seq) - start
    q = (1 << period_len) - 1

    # Prefix contribution before the cycle.
    val = 0
    for i in range(start):
        val = (val << 1) + seq[i]
    prefix_num = val << 1

    # Cycle contribution.
    val = 0
    for i in range(start, len(seq)):
        val = (val << 1) + seq[i]
    period_num = val << 1

    numerator = prefix_num * q + period_num
    denominator = (1 << start) * q

    g = math.gcd(numerator, denominator)
    numerator //= g
    denominator //= g

    print(f"{numerator}/{denominator}")


if __name__ == "__main__":
    solve()