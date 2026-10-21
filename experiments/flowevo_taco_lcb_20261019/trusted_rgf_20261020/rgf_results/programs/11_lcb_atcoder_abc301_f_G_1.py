import sys

MOD = 998244353


def main():
    S = sys.stdin.readline().strip()
    n = len(S)

    # H[i] = number of ways to assign S[i:] such that it has the form
    # U+ L* (at least one uppercase, then only lowercase after the last uppercase).
    H = [0] * (n + 1)
    lower_product_after = 1

    for i in range(n - 1, -1, -1):
        c = S[i]
        if c == '?':
            upper_ways = 26
            lower_ways = 26
        elif 'A' <= c <= 'Z':
            upper_ways = 1
            lower_ways = 0
        else:
            upper_ways = 0
            lower_ways = 1

        H[i] = upper_ways * ((lower_product_after + H[i + 1]) % MOD) % MOD
        lower_product_after = lower_ways * lower_product_after % MOD

    all_lower = lower_product_after
    ans = (all_lower + H[0]) % MOD

    limit = max(n, 26)

    fact = [1] * (limit + 1)
    pow26 = [1] * (limit + 1)

    for i in range(1, limit + 1):
        fact[i] = fact[i - 1] * i % MOD
        pow26[i] = pow26[i - 1] * 26 % MOD

    invfact = [1] * (limit + 1)
    invfact[limit] = pow(fact[limit], MOD - 2, MOD)

    for i in range(limit, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    question_count = 0
    fixed_upper_count = 0
    upper_mask = 0
    duplicate_fixed_upper = False

    # F = number of assignments of the processed prefix such that
    # all uppercase letters in the prefix are distinct.
    F = 1

    for i, c in enumerate(S):
        if c == '?':
            lower_ways = 26
        elif 'A' <= c <= 'Z':
            lower_ways = 0
        else:
            lower_ways = 1

        if F and lower_ways:
            ans = (ans + F * lower_ways % MOD * H[i + 1]) % MOD

        # Add S[i] to prefix statistics.
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
                term = base * invfact[t] % MOD
                term = term * invfact[question_count - t] % MOD
                term = term * invfact[available - t] % MOD
                term = term * pow26[question_count - t] % MOD

                total += term
                if total >= MOD:
                    total -= MOD

            F = total

    print(ans % MOD)


if __name__ == "__main__":
    main()
