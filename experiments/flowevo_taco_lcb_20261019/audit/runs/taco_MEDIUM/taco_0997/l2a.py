import sys
import math

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
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
            g = math.gcd(g, angles[i + 1] - angles[i])

        wrap_gap = angles[0] + 360 - angles[-1]
        g = math.gcd(g, wrap_gap)

        slices = 360 // g
        answers.append(str(slices - n))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()