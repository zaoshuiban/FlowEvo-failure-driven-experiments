import sys

MOD = 998244353

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    K = data[0]
    C = data[1:27]

    fact = [1] * (K + 1)
    for i in range(1, K + 1):
        fact[i] = fact[i - 1] * i % MOD

    invfact = [1] * (K + 1)
    invfact[K] = pow(fact[K], MOD - 2, MOD)
    for i in range(K, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    dp = [0] * (K + 1)
    dp[0] = 1

    for c in C:
        c = min(c, K)
        if c == 0:
            continue

        ndp = [0] * (K + 1)

        for length, val in enumerate(dp):
            if val == 0:
                continue

            limit = min(c, K - length)
            for x in range(limit + 1):
                ndp[length + x] = (ndp[length + x] + val * invfact[x]) % MOD

        dp = ndp

    ans = 0
    for length in range(1, K + 1):
        ans = (ans + dp[length] * fact[length]) % MOD

    print(ans)

if __name__ == "__main__":
    main()