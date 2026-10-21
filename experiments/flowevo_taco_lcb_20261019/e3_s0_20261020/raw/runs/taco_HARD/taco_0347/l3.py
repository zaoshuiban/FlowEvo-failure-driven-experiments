import sys
from math import isqrt


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    max_a = max(a)

    # spf[x] will contain some prime divisor of x for composite x, and 0 for primes.
    spf = [0] * (max_a + 1)
    limit = isqrt(max_a)

    for i in range(2, limit + 1):
        if spf[i] == 0:  # i is prime
            for j in range(i * i, max_a + 1, i):
                spf[j] = i

    ans1 = [-1] * n
    ans2 = [-1] * n

    for idx, value in enumerate(a):
        p = spf[value]

        # value is prime, so no valid pair exists.
        if p == 0:
            continue

        x = value
        while x % p == 0:
            x //= p

        # value is a prime power, so no valid pair exists.
        if x == 1:
            continue

        ans1[idx] = p
        ans2[idx] = x

    sys.stdout.write(" ".join(map(str, ans1)) + "\n")
    sys.stdout.write(" ".join(map(str, ans2)) + "\n")


if __name__ == "__main__":
    main()