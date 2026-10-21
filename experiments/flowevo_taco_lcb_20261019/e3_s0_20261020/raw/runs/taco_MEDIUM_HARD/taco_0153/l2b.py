import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    total = sum(a)

    if total <= 1:
        print(-1)
        return

    # Find distinct prime factors of total.
    x = total
    primes = []
    d = 2
    while d * d <= x:
        if x % d == 0:
            primes.append(d)
            while x % d == 0:
                x //= d
        d += 1 if d == 2 else 2
    if x > 1:
        primes.append(x)

    answer = 10**30

    for p in primes:
        carry = 0
        cost = 0

        for value in a:
            carry = (carry + value) % p
            if carry != 0:
                cost += min(carry, p - carry)

        answer = min(answer, cost)

    print(answer)


if __name__ == "__main__":
    solve()