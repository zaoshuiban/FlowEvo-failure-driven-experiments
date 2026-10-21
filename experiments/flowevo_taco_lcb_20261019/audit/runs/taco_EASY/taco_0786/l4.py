import sys
import math

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        A, B, C = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        if C <= 0:
            ans.append("0/1")
            continue

        if C >= A + B:
            ans.append("1/1")
            continue

        den = 2 * A * B
        mn = min(A, B)
        mx = max(A, B)

        if C <= mn:
            num = C * C
        elif C <= mx:
            num = 2 * C * mn - mn * mn
        else:
            num = 2 * A * B - (A + B - C) * (A + B - C)

        g = math.gcd(num, den)
        ans.append(f"{num // g}/{den // g}")

    sys.stdout.write("\n".join(ans))
    if ans:
        sys.stdout.write("\n")

if __name__ == "__main__":
    solve()