import sys
from collections import Counter


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    b = data[1:]
    del data

    max_b = max(b)

    # Sieve primes up to max(b)
    is_prime = bytearray(b'\x01') * (max_b + 1)
    is_prime[0] = 0
    if max_b >= 1:
        is_prime[1] = 0

    limit = int(max_b ** 0.5)
    for i in range(2, limit + 1):
        if is_prime[i]:
            start = i * i
            count = (max_b - start) // i + 1
            is_prime[start:max_b + 1:i] = b'\x00' * count

    primes = [i for i in range(2, max_b + 1) if is_prime[i]]
    prime_index = {p: i + 1 for i, p in enumerate(primes)}
    del primes

    # Smallest prime factor up to 2 * 10^5
    MAX_A = 200000
    spf = list(range(MAX_A + 1))
    limit_a = int(MAX_A ** 0.5)

    for i in range(2, limit_a + 1):
        if spf[i] == i:
            for j in range(i * i, MAX_A + 1, i):
                if spf[j] == j:
                    spf[j] = i

    cnt = Counter(b)
    del b

    answer = []

    for x in sorted(cnt.keys(), reverse=True):
        while cnt[x] > 0:
            if is_prime[x]:
                idx = prime_index[x]
                answer.append(idx)
                cnt[x] -= 1
                cnt[idx] -= 1
            else:
                answer.append(x)
                cnt[x] -= 1
                greatest_proper_divisor = x // spf[x]
                cnt[greatest_proper_divisor] -= 1

    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    main()