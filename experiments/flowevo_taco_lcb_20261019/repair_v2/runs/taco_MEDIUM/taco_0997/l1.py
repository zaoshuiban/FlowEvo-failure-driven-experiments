import sys
import math

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        angles = data[idx:idx + n]
        idx += n

        angles.sort()

        g = 0
        for i in range(n - 1):
            gap = angles[i + 1] - angles[i]
            g = math.gcd(g, gap)

        wrap_gap = angles[0] + 360 - angles[-1]
        g = math.gcd(g, wrap_gap)

        answers.append(str(360 // g - n))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()