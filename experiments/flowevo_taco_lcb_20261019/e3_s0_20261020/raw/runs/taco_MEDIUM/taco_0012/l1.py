import sys

MOD = 1_000_000_007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    tests = []
    max_n = 0

    for _ in range(t):
        U, V, K, P = data[idx], data[idx + 1], data[idx + 2], data[idx + 3]
        idx += 4
        tests.append((U, V, K, P))
        max_n = max(max_n, U * P)

    fact = [1] * (max_n + 1)
    for i in range(1, max_n + 1):
        fact[i] = fact[i - 1] * i % MOD

    inv_fact = [1] * (max_n + 1)
    inv_fact[max_n] = pow(fact[max_n], MOD - 2, MOD)

    for i in range(max_n, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    def comb(n, r):
        if r < 0 or r > n:
            return 0
        return fact[n] * inv_fact[r] % MOD * inv_fact[n - r] % MOD

    answers = []

    for U, V, K, P in tests:
        total_ways = comb(U * P, V * P)
        sym_ways = comb(U, V)

        diff = (total_ways - sym_ways) % MOD
        inv_p = pow(P, MOD - 2, MOD)

        if K == 0:
            ans = (sym_ways + diff * inv_p) % MOD
        else:
            ans = diff * inv_p % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()