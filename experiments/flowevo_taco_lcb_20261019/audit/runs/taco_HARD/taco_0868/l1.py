import sys
import math

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    result = []

    for i in range(1, t + 1):
        n = data[i]
        ans = 1.0 / (2.0 * math.sin(math.pi / (4.0 * n)))
        result.append(f"{ans:.10f}")

    sys.stdout.write("\n".join(result))

if __name__ == "__main__":
    solve()