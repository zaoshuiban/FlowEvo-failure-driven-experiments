import sys
import math


def build_sequence(k):
    if k == 1:
        return [1]
    if k == 2:
        return [3, 4]

    q = math.isqrt(k - 1) + 1

    while True:
        d = q * q - k
        max_b = min(k, d // 8)
        start_mod = (2 * d) % 3

        b = max_b - ((max_b - start_mod) % 3)

        while b >= 0:
            rem = d - 8 * b
            if rem % 3 == 0:
                a = rem // 3
                if a + b <= k:
                    seq = [3] * b + [2] * a + [1] * (k - a - b)
                    return seq
            b -= 3

        q += 1


def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n, m = map(int, data[:2])

    rows = build_sequence(n)
    cols = build_sequence(m)

    result = []
    for x in rows:
        result.append(" ".join(str(x * y) for y in cols))

    sys.stdout.write("\n".join(result))


if __name__ == "__main__":
    main()