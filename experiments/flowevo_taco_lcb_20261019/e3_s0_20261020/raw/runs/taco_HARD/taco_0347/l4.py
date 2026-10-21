import sys
from math import isqrt


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    max_a = max(a)
    size = (max_a >> 1) + 1

    # spf_odd[k] stores some prime divisor of the odd number 2*k + 1.
    # 0 means the odd number is prime.
    spf_odd = [0] * size

    limit = isqrt(max_a)
    for p in range(3, limit + 1, 2):
        if spf_odd[p >> 1] == 0:  # p is prime
            start = (p * p) >> 1
            for k in range(start, size, p):
                spf_odd[k] = p

    ans1 = [-1] * n
    ans2 = [-1] * n

    for i, value in enumerate(a):
        if value & 1:
            p = spf_odd[value >> 1]
            if p == 0:
                continue
        else:
            p = 2

        x = value
        while x % p == 0:
            x //= p

        if x > 1:
            ans1[i] = p
            ans2[i] = x

    sys.stdout.write(" ".join(map(str, ans1)) + "\n")
    sys.stdout.write(" ".join(map(str, ans2)) + "\n")


if __name__ == "__main__":
    main()