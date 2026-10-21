import sys
import math


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    queries = []
    idx = 1
    max_n = 0

    for _ in range(t):
        m = data[idx]
        n = data[idx + 1]
        idx += 2
        queries.append((m, n))
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

    base_primes = [i for i in range(2, limit + 1) if sieve[i]]

    output = []

    for case_idx, (m, n) in enumerate(queries):
        if case_idx > 0:
            output.append("")

        low = max(m, 2)
        if low > n:
            continue

        size = n - low + 1
        is_prime = bytearray(b'\x01') * size

        for prime in base_primes:
            if prime * prime > n:
                break

            start = ((low + prime - 1) // prime) * prime
            if start < prime * prime:
                start = prime * prime

            if start <= n:
                for value in range(start, n + 1, prime):
                    is_prime[value - low] = 0

        for i, value in enumerate(is_prime):
            if value:
                output.append(str(low + i))

    if output:
        sys.stdout.write("\n".join(output))
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()