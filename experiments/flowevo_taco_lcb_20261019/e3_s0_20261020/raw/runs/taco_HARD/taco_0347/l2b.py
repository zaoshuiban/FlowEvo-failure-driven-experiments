import sys
from math import isqrt


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]
    max_a = max(a)

    spf = [0] * (max_a + 1)
    limit = isqrt(max_a)

    # For every composite number, store any prime divisor.
    for i in range(2, limit + 1):
        if spf[i] == 0:
            for j in range(i * i, max_a + 1, i):
                spf[j] = i

    ans1 = []
    ans2 = []

    append1 = ans1.append
    append2 = ans2.append

    for value in a:
        p = spf[value]

        if p == 0:
            append1(-1)
            append2(-1)
        else:
            x = value
            power = 1

            while x % p == 0:
                x //= p
                power *= p

            if x == 1:
                append1(-1)
                append2(-1)
            else:
                append1(power)
                append2(x)

    sys.stdout.write(" ".join(map(str, ans1)) + "\n")
    sys.stdout.write(" ".join(map(str, ans2)) + "\n")


if __name__ == "__main__":
    main()