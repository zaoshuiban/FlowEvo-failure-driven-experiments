import sys
import math


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        n = int(data[i])
        side = 1.0 / (2.0 * math.sin(math.pi / (4.0 * n)))
        answers.append(f"{side:.12f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()