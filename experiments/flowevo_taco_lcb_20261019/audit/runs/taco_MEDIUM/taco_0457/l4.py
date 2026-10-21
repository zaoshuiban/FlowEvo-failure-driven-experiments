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
        m, n, p, q = data[idx], data[idx + 1], data[idx + 2], data[idx + 3]
        idx += 4

        x = m - p
        y = n - q

        a = min(x, y)
        b = max(x, y)
        d = b - a

        # Wythoff Nim P-position condition:
        # (a, b) is losing iff a == floor(d * phi),
        # where d = b - a and phi = (1 + sqrt(5)) / 2.
        floor_d_phi = (d + math.isqrt(5 * d * d)) // 2

        if a == floor_d_phi:
            ans.append("Bob")
        else:
            ans.append("Alice")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()