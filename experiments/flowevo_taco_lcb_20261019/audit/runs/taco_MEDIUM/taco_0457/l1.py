import sys
from math import isqrt

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

        a, b = min(x, y), max(x, y)
        d = b - a

        # Wythoff Nim P-position condition:
        # P-positions are (floor(k*phi), floor(k*phi^2)).
        # For min = a, max = b, let d = b - a.
        # Then it is a P-position iff a == floor(d * phi).
        expected = (d + isqrt(5 * d * d)) // 2

        if a == expected:
            ans.append("Bob")
        else:
            ans.append("Alice")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()