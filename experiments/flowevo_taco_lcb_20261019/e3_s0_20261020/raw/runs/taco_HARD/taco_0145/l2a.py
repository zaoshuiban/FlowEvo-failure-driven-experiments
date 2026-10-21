import sys
import math


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])

    # Find the eventually periodic sequence r_k = (2^k mod n).
    seen = [-1] * n
    residues = []

    r = 1 % n
    k = 0

    while seen[r] == -1:
        seen[r] = k
        residues.append(r)
        r = (r * 2) % n
        k += 1

    cycle_start = seen[r]
    cycle_len = len(residues) - cycle_start

    # Prefix before the cycle.
    prefix_value = 0
    for i in range(cycle_start):
        prefix_value = (prefix_value << 1) + residues[i]
    prefix_num = prefix_value << 1

    # Periodic part.
    cycle_value = 0
    for i in range(cycle_start, cycle_start + cycle_len):
        cycle_value = (cycle_value << 1) + residues[i]
    cycle_num = cycle_value << 1

    pow_cycle = 1 << cycle_len
    pow_start = 1 << cycle_start

    cycle_factor = pow_cycle - 1

    numerator = prefix_num * cycle_factor + cycle_num
    denominator = pow_start * cycle_factor

    g = math.gcd(numerator, denominator)
    numerator //= g
    denominator //= g

    print(f"{numerator}/{denominator}")


if __name__ == "__main__":
    main()