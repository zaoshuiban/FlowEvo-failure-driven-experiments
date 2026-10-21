import sys
import math

MOD = 1_000_000_007

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for i in range(1, t + 1):
        n = data[i]

        if n < 2:
            ans.append("0")
            continue

        # Largest m such that m * (m + 1) / 2 < n
        m = (math.isqrt(8 * n - 7) - 1) // 2

        # sum_{k=1..m} k * (k + 1) / 2
        s1 = m * (m + 1) * (m + 2) // 6

        # sum_{k=1..m} (k * (k + 1) / 2)^2
        s2 = m * (m + 1) * (m + 2) * (3 * m * m + 6 * m + 1) // 60

        res = ((n % MOD) * (s1 % MOD) - (s2 % MOD)) % MOD
        ans.append(str(res))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()