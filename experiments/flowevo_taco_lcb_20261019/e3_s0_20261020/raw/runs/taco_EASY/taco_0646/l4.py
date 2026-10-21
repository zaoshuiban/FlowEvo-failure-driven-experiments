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
    sieve[0:2] = b'\x00\x00'

    for i in range(2, isqrt(limit) + 1):
        if sieve[i]:
            start = i * i
            count = ((limit - start) // i) + 1
            sieve[start:limit + 1:i] = b'\x00' * count

    base_primes = [i for i in range(2, limit + 1) if sieve[i]]

    out_lines = []

    for m, n in tests:
        size = n - m + 1
        is_prime = bytearray(b'\x01') * size

        if m == 1:
            is_prime[0] = 0

        for p in base_primes:
            if p * p > n:
                break

            start = max(p * p, ((m + p - 1) // p) * p)
            if start > n:
                continue

            offset = start - m
            count = ((n - start) // p) + 1
            is_prime[offset:size:p] = b'\x00' * count

        out_lines.extend(str(m + i) for i, flag in enumerate(is_prime) if flag)
        out_lines.append("")

    if out_lines:
        sys.stdout.write("\n".join(out_lines))
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()