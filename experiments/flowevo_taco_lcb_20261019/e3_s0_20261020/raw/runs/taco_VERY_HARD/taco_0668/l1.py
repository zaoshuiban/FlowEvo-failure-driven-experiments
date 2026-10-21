import sys
import math


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n, l, r = map(int, data)

    if n == 1:
        print(r - l + 1)
        return

    if n == 2:
        m = r - l + 1
        print(m * (m - 1))
        return

    # Since r <= 10^7, for n >= 25 even the smallest ratio > 1
    # using p >= 2 gives p^(n-1) >= 2^24 > 10^7.
    if n >= 25:
        print(0)
        return

    e = n - 1

    # Find maximum p such that p^e <= r.
    P = 1
    p = 2
    while True:
        value = pow(p, e)
        if value > r:
            break
        P = p
        p += 1

    if P < 2:
        print(0)
        return

    powers = [0] * (P + 1)
    for i in range(1, P + 1):
        powers[i] = pow(i, e)

    increasing = 0
    gcd = math.gcd

    for p in range(2, P + 1):
        p_power = powers[p]
        max_c = r // p_power

        for q in range(1, p):
            q_power = powers[q]
            min_c = (l + q_power - 1) // q_power

            if min_c <= max_c and gcd(p, q) == 1:
                increasing += max_c - min_c + 1

    # Every increasing progression has a reversed decreasing counterpart.
    print(increasing * 2)


if __name__ == "__main__":
    main()