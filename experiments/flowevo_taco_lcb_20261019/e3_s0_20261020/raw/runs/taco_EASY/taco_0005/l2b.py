import sys
from math import isqrt

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    out = []
    idx = 1

    for _ in range(t):
        n = data[idx]
        idx += 1

        ans = [0] * n
        r = n - 1

        while r >= 0:
            k = isqrt(r)
            if k * k < r:
                k += 1
            square = k * k
            l = square - r

            for i in range(l, r + 1):
                ans[i] = square - i

            r = l - 1

        out.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    solve()