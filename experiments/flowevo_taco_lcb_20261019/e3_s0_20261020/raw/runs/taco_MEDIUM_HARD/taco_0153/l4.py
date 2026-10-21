import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    total = sum(a)

    if total == 0:
        print(0)
        return

    if total == 1:
        print(-1)
        return

    # Find distinct prime divisors of total.
    x = total
    primes = []

    if x % 2 == 0:
        primes.append(2)
        while x % 2 == 0:
            x //= 2

    d = 3
    while d * d <= x:
        if x % d == 0:
            primes.append(d)
            while x % d == 0:
                x //= d
        d += 2

    if x > 1:
        primes.append(x)

    answer = None

    for p in primes:
        prefix = 0
        cost = 0

        for value in a:
            prefix += value
            r = prefix % p
            if r:
                cost += min(r, p - r)

        if answer is None or cost < answer:
            answer = cost

    print(answer)


if __name__ == "__main__":
    solve()