import sys
import math

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    idx = 1
    answers = []

    for _ in range(n):
        A, B, C = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        num = C * C

        v = C - A
        if v > 0:
            num -= v * v

        v = C - B
        if v > 0:
            num -= v * v

        v = C - A - B
        if v > 0:
            num += v * v

        den = 2 * A * B

        g = math.gcd(num, den)
        answers.append(f"{num // g}/{den // g}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()