import sys
import math

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        m, n, p, q = data[idx:idx + 4]
        idx += 4

        x = m - p
        y = n - q

        if x > y:
            x, y = y, x

        d = y - x

        # Wythoff Nim losing positions satisfy:
        # x = floor(d * phi), where phi = (1 + sqrt(5)) / 2
        expected_x = (d + math.isqrt(5 * d * d)) // 2

        if x == expected_x:
            ans.append("Bob")
        else:
            ans.append("Alice")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()