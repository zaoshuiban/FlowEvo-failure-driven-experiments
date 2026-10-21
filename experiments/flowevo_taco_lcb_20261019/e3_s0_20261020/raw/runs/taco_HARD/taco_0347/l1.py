import sys
from math import isqrt
from array import array


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]

    # n itself may be larger than all a_i, but that is still a safe upper bound.
    N = max(data)

    # spf[x >> 1] stores some prime divisor for the odd number x = 2 * index + 1.
    m = (N >> 1) + 1
    spf = [0] * m

    limit = isqrt(N)
    for p in range(3, limit + 1, 2):
        if spf[p >> 1] == 0:  # p is prime
            start = (p * p) >> 1
            for idx in range(start, m, p):
                spf[idx] = p

    ans1 = array('i')
    ans2 = array('i')
    add1 = ans1.append
    add2 = ans2.append

    for i in range(1, n + 1):
        a = data[i]

        if a & 1:
            p = spf[a >> 1]
            if p == 0:  # a is prime
                add1(-1)
                add2(-1)
                continue
        else:
            p = 2

        rest = a

        if p == 2:
            while (rest & 1) == 0:
                rest >>= 1
        else:
            while rest % p == 0:
                rest //= p

        if rest == 1:
            add1(-1)
            add2(-1)
        else:
            add1(rest)
            add2(a // rest)

    sys.stdout.write(' '.join(map(str, ans1)))
    sys.stdout.write('\n')
    sys.stdout.write(' '.join(map(str, ans2)))
    sys.stdout.write('\n')


if __name__ == "__main__":
    main()