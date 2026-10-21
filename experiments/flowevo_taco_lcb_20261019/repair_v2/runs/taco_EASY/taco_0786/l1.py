import sys
import math


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    idx = 1
    results = []

    for _ in range(n):
        A, B, C = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        ca = max(C - A, 0)
        cb = max(C - B, 0)
        cab = max(C - A - B, 0)

        numerator = C * C - ca * ca - cb * cb + cab * cab
        denominator = 2 * A * B

        g = math.gcd(numerator, denominator)
        results.append(f"{numerator // g}/{denominator // g}")

    sys.stdout.write("\n".join(results))


if __name__ == "__main__":
    main()