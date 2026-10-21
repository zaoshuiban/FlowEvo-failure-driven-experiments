import sys
from math import gcd

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)

        base = next(it)
        g = 0

        for _ in range(n - 1):
            x = next(it)
            g = gcd(g, abs(x - base))

        if (k - base) % g == 0:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()