import sys
import math


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    tests = []
    max_n = 0
    idx = 1

    for _ in range(t):
        m = data[idx]
        n = data[idx + 1]
        idx += 2
        tests.append((m, n))
        if n > max_n:
            max_n = n

    limit = math.isqrt(max_n)

    sieve = bytearray(b'\x01') * (limit + 1)
    if limit >= 0:
        sieve[0] = 0
    if limit >= 1:
        sieve[1] = 0

    for i in range(2, math.isqrt(limit) + 1):
        if sieve[i]:
            start = i * i
            sieve[start:limit + 1:i] = b'\x00' * (((limit - start) // i) + 1)

    primes = [i for i in range(2, limit + 1) if sieve[i]]

    answers = []

    for m, n in tests:
        is_prime = bytearray(b'\x01') * (n - m + 1)

        if m == 1:
            is_prime[0] = 0

        for p in primes:
            if p * p > n:
                break

            start = ((m + p - 1) // p) * p
            if start < p * p:
                start = p * p

            if start <= n:
                is_prime[start - m:n + 1 - m:p] = b'\x00' * (((n - start) // p) + 1)

        result = [str(m + i) for i, value in enumerate(is_prime) if value]
        answers.append('\n'.join(result))

    sys.stdout.write('\n\n'.join(answers))


if __name__ == "__main__":
    main()