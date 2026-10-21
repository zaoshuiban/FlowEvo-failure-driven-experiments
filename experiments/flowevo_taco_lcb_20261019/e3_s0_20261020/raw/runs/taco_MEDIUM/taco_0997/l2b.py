import sys
import math

def solve() -> None:
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

        base = angles[0]
        g = 360

        for angle in angles[1:]:
            g = math.gcd(g, abs(angle - base))

        slices = 360 // g
        answers.append(str(slices - n))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()