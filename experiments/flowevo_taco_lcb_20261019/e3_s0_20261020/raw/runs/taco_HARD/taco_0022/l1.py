import sys

MOD = 998244353

def solve() -> None:
    n, k = map(int, sys.stdin.buffer.readline().split())

    if k == 0:
        ans = 1
        for i in range(2, n + 1):
            ans = ans * i % MOD
        print(ans)
        return

    if k >= n:
        print(0)
        return

    m = n - k  # number of used columns when all rows are occupied

    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i % MOD

    inv_fact = [1] * (n + 1)
    inv_fact[n] = pow(fact[n], MOD - 2, MOD)
    for i in range(n, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    # Number of surjective functions from n rows onto m fixed columns:
    # sum_{i=0}^{m} (-1)^i * C(m, i) * (m - i)^n
    surj = 0
    fact_m = fact[m]

    for i in range(m + 1):
        comb = fact_m * inv_fact[i] % MOD * inv_fact[m - i] % MOD
        term = comb * pow(m - i, n, MOD) % MOD

        if i & 1:
            surj -= term
        else:
            surj += term

    surj %= MOD

    choose_columns = fact[n] * inv_fact[m] % MOD * inv_fact[n - m] % MOD
    answer = 2 * choose_columns % MOD * surj % MOD

    print(answer)


if __name__ == "__main__":
    solve()