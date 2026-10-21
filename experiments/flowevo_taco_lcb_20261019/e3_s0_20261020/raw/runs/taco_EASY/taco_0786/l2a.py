import sys
import math

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    idx = 1
    answers = []

    for _ in range(n):
        A, B, C = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        numerator = C * C

        if C > A:
            numerator -= (C - A) * (C - A)
        if C > B:
            numerator -= (C - B) * (C - B)

        remaining = C - A - B
        if remaining > 0:
            numerator += remaining * remaining

        denominator = 2 * A * B

        g = math.gcd(numerator, denominator)
        answers.append(f"{numerator // g}/{denominator // g}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()