import sys
from math import gcd

def solve():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        arr = [next(it) for _ in range(n)]

        if n == 1:
            answers.append("1")
            continue

        total = sum(arr)

        pref = [0] * (n + 1)
        g = 0
        for i, x in enumerate(arr):
            g = gcd(g, x)
            pref[i + 1] = g

        # Case where no salary is changed
        ans = total // g

        # Try changing each employee's salary
        suffix_gcd = 0
        for i in range(n - 1, -1, -1):
            gcd_except_i = gcd(pref[i], suffix_gcd)
            notes = 1 + (total - arr[i]) // gcd_except_i
            if notes < ans:
                ans = notes
            suffix_gcd = gcd(suffix_gcd, arr[i])

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()