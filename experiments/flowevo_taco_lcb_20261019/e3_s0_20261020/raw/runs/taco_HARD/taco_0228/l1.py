import sys


def main():
    data = sys.stdin.buffer.read()
    length = len(data)
    idx = 0

    while idx < length and data[idx] <= 32:
        idx += 1

    n = 0
    while idx < length and data[idx] > 32:
        n = n * 10 + data[idx] - 48
        idx += 1

    a = [0] * n
    total = 0

    for i in range(n):
        while idx < length and data[idx] <= 32:
            idx += 1

        x = 0
        while idx < length and data[idx] > 32:
            x = x * 10 + data[idx] - 48
            idx += 1

        a[i] = x
        total += x

    del data

    if total < 2:
        print(-1)
        return

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

    ans = 10**30
    limit = n - 1

    for p in primes:
        cur = 0
        cost = 0

        for i in range(limit):
            cur += a[i]
            cur %= p

            if cur * 2 <= p:
                cost += cur
            else:
                cost += p - cur

            if cost >= ans:
                break

        if cost < ans:
            ans = cost
            if ans == 0:
                break

    print(ans)


if __name__ == "__main__":
    main()