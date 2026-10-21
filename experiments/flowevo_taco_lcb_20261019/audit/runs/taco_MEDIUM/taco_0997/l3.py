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

        angles = sorted(set(angles))
        m = len(angles)

        if m <= 1:
            answers.append("1" if m == 1 else "0")
            continue

        g = 0
        for i in range(m):
            gap = (angles[(i + 1) % m] - angles[i]) % 360
            g = math.gcd(g, gap)

        total_slices = 360 // g
        answers.append(str(total_slices - m))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()