import sys
from math import isqrt


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    tests = []
    max_n = 1
    idx = 1

    for _ in range(t):
        m = data[idx]
        n = data[idx + 1]
        idx += 2
        tests.append((m, n))
        if n > max_n:
            max_n = n

    limit = isqrt(max_n) + 1
    sieve = bytearray(b'\x01') * (limit + 1)
    sieve[0] = 0
    if limit >= 1:
        sieve[1] = 0

    for i in range(2, isqrt(limit) + 1):
        if sieve[i]:
            start = i * i
            sieve[start:limit + 1:i] = b'\x00' * (((limit - start) // i) + 1)

    base_primes = [i for i in range(2, limit + 1) if sieve[i]]

    output_blocks = []

    for m, n in tests:
        size = n - m + 1
        is_prime = bytearray(b'\x01') * size

        if m < 2:
            for value in range(m, min(2, n + 1)):
                is_prime[value - m] = 0

        for p in base_primes:
            if p * p > n:
                break

            start = max(p * p, ((m + p - 1) // p) * p)
            if start > n:
                continue

            count = ((n - start) // p) + 1
            is_prime[start - m:n + 1:p] = b'\x00' * count

        primes = [str(m + i) for i, flag in enumerate(is_prime) if flag]
        output_blocks.append('\n'.join(primes))

    sys.stdout.write('\n\n'.join(output_blocks))


if __name__ == "__main__":
    main()