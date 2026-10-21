import sys
import math

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        p = [0] * n
        r = n - 1

        while r >= 0:
            root = math.isqrt(r)
            if root * root < r:
                root += 1

            square = root * root
            l = square - r

            for i in range(l, r + 1):
                p[i] = square - i

            r = l - 1

        answers.append(" ".join(map(str, p)))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()