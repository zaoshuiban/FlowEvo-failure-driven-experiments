import sys
import math

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    output = []

    for _ in range(t):
        n = data[pos]
        pos += 1

        ans = [0] * n
        r = n - 1

        while r >= 0:
            k = math.isqrt(r)
            if k * k < r:
                k += 1

            square = k * k
            l = square - r

            for i in range(l, r + 1):
                ans[i] = square - i

            r = l - 1

        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()