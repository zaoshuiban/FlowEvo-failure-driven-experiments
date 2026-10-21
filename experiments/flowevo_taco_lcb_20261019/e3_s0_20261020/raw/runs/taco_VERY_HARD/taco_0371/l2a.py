import sys
from array import array

MOD = 1_000_000_007

def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])

    # Maximum number of prime factors with multiplicity for numbers <= n.
    K = n.bit_length() - 1  # floor(log2(n))

    # Modular inverses up to n.
    inv = array('I', [0]) * (n + 1)
    inv[1] = 1
    for i in range(2, n + 1):
        inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD

    # Smallest prime factor sieve.
    spf = array('I', range(n + 1))
    limit = int(n ** 0.5)
    for i in range(2, limit + 1):
        if spf[i] == i:
            for j in range(i * i, n + 1, i):
                if spf[j] == j:
                    spf[j] = i

    # dp[a] = sum of probabilities of all maximal gcd chains starting from a.
    dp = array('I', [0]) * (n + 1)
    dp[1] = 1

    total = 0

    for a in range(2, n + 1):
        x = a
        qa = n // a
        inv_den = inv[n - qa]

        cur = 0
        omega = 0

        while x > 1:
            p = spf[x]
            b = a // p

            numerator = n // b - qa
            term = numerator * inv_den % MOD
            term = term * dp[b] % MOD
            cur += term

            while x % p == 0:
                x //= p
                omega += 1

        cur %= MOD
        dp[a] = cur

        if omega == K:
            total += cur
            if total >= MOD:
                total -= MOD

    fact = 1
    for i in range(2, n):
        fact = fact * i % MOD

    answer = fact * total % MOD
    print(answer)


if __name__ == "__main__":
    main()