import sys
from math import isqrt
from array import array


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]
    del data

    max_a = max(a)

    # spf[x] will be the smallest prime factor of x, but only for composite x.
    # For composite x <= 10^7, its smallest prime factor is at most sqrt(10^7) < 3163,
    # so unsigned short is enough.
    spf = array('H', [0]) * (max_a + 1)
    limit = isqrt(max_a)

    for i in range(2, limit + 1):
        if spf[i] == 0:
            start = i * i
            for j in range(start, max_a + 1, i):
                if spf[j] == 0:
                    spf[j] = i

    ans1 = [''] * n
    ans2 = [''] * n

    for idx, value in enumerate(a):
        p = spf[value]

        # If spf[value] == 0, value is prime, hence a prime power.
        if p == 0:
            ans1[idx] = "-1"
            ans2[idx] = "-1"
            continue

        x = value
        power = 1

        while x % p == 0:
            x //= p
            power *= p

        # value is a power of a single prime.
        if x == 1:
            ans1[idx] = "-1"
            ans2[idx] = "-1"
        else:
            ans1[idx] = str(power)
            ans2[idx] = str(value // power)

    sys.stdout.write(" ".join(ans1) + "\n")
    sys.stdout.write(" ".join(ans2) + "\n")


if __name__ == "__main__":
    main()