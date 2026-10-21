import sys
import math


def construct(n: int):
    p = [0] * n
    r = n - 1

    while r >= 0:
        s = math.isqrt(r)
        if s * s < r:
            s += 1

        square = s * s
        l = square - r

        for i in range(l, r + 1):
            p[i] = square - i

        r = l - 1

    return p


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        p = construct(n)
        answers.append(" ".join(map(str, p)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()