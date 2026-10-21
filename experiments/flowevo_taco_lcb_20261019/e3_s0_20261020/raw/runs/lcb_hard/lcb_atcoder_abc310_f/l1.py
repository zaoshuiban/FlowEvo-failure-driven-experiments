import sys

MOD = 998244353

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    A = data[1:1 + N]

    BITS = 11  # sums 0..10
    SIZE = 1 << BITS
    MASK = SIZE - 1

    dp = [0] * SIZE
    dp[1] = 1  # only sum 0 is achievable

    for a in A:
        inv_a = pow(a, MOD - 2, MOD)
        upto = min(a, 10)

        ndp = [0] * SIZE
        prob_greater = (a - 10) * inv_a % MOD if a > 10 else 0

        for mask, prob in enumerate(dp):
            if prob == 0:
                continue

            for k in range(1, upto + 1):
                next_mask = mask | ((mask << k) & MASK)
                ndp[next_mask] = (ndp[next_mask] + prob * inv_a) % MOD

            if prob_greater:
                ndp[mask] = (ndp[mask] + prob * prob_greater) % MOD

        dp = ndp

    target_bit = 1 << 10
    ans = 0
    for mask, prob in enumerate(dp):
        if mask & target_bit:
            ans = (ans + prob) % MOD

    print(ans)


if __name__ == "__main__":
    main()