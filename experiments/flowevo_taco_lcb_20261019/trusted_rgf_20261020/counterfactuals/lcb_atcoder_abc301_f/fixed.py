import sys

MOD = 998244353

def main():
    S = sys.stdin.readline().strip()
    n = len(S)

    # H[i]: number of ways to assign positions i..n-1 as U^+ L^*
    # where the first character of the suffix must be uppercase.
    H = [0] * (n + 1)
    lw_after = 1  # product of lowercase-ways for positions after current position

    for i in range(n - 1, -1, -1):
        c = S[i]
        if c == '?':
            u = 26
            lw = 26
        elif 'A' <= c <= 'Z':
            u = 1
            lw = 0
        else:
            u = 0
            lw = 1

        H[i] = u * ((lw_after + H[i + 1]) % MOD) % MOD
        lw_after = lw * lw_after % MOD

    all_lower = lw_after
    ans = (all_lower + H[0]) % MOD

    n = max(n, 26)  # factorial indices include the entire alphabet
    fact = [1] * (n + 1)
    pow26 = [1] * (n + 1)

    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i % MOD
        pow26[i] = pow26[i - 1] * 26 % MOD

    invfact = [1] * (n + 1)
    invfact[n] = pow(fact[n], MOD - 2, MOD)

    for i in range(n, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    # F = number of assignments of the processed prefix such that
    # all uppercase letters in it are distinct.
    question_count = 0
    fixed_upper_count = 0
    upper_mask = 0
    duplicate_fixed_upper = False
    F = 1

    invf = invfact
    pw = pow26

    for i, c in enumerate(S):
        if c == '?':
            low_ways = 26
        elif 'A' <= c <= 'Z':
            low_ways = 0
        else:
            low_ways = 1

        if F and low_ways:
            ans = (ans + F * low_ways % MOD * H[i + 1]) % MOD

        # Add S[i] to the prefix statistics.
        if c == '?':
            question_count += 1
        elif 'A' <= c <= 'Z':
            idx = ord(c) - ord('A')
            bit = 1 << idx
            if upper_mask & bit:
                duplicate_fixed_upper = True
            else:
                upper_mask |= bit
                fixed_upper_count += 1

        # Compute F for the prefix including S[i].
        if duplicate_fixed_upper:
            F = 0
        else:
            available = 26 - fixed_upper_count
            max_t = min(question_count, available)

            base = fact[question_count] * fact[available] % MOD
            total = 0

            for t in range(max_t + 1):
                term = base * invf[t] % MOD
                term = term * invf[question_count - t] % MOD
                term = term * invf[available - t] % MOD
                term = term * pw[question_count - t] % MOD

                total += term
                if total >= MOD:
                    total -= MOD

            F = total

    print(ans % MOD)


if __name__ == "__main__":
    main()