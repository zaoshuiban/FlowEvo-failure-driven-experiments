import sys

MOD = 998244353


def main():
    S = sys.stdin.readline().strip()
    n = len(S)

    # H[i] = number of ways to assign S[i..n-1] so that it has the form
    # U+ L* and S[i] is the first uppercase character.
    H = [0] * (n + 1)
    lower_after = 1  # product of lowercase choices for positions after i

    for i in range(n - 1, -1, -1):
        c = S[i]
        if c == '?':
            u = 26
            low = 26
        elif 'A' <= c <= 'Z':
            u = 1
            low = 0
        else:
            u = 0
            low = 1

        H[i] = u * ((lower_after + H[i + 1]) % MOD) % MOD
        lower_after = low * lower_after % MOD

    all_lower = lower_after
    ans = (all_lower + H[0]) % MOD

    # We need factorials up to max(n, 26), because 26 - fixed_upper_count
    # can be larger than n when n is small.
    max_n = max(n, 26)
    fact = [1] * (max_n + 1)
    pow26 = [1] * (max_n + 1)

    for i in range(1, max_n + 1):
        fact[i] = fact[i - 1] * i % MOD
        pow26[i] = pow26[i - 1] * 26 % MOD

    invfact = [1] * (max_n + 1)
    invfact[max_n] = pow(fact[max_n], MOD - 2, MOD)

    for i in range(max_n, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    question_count = 0
    fixed_upper_count = 0
    upper_mask = 0
    duplicate_fixed_upper = False
    F = 1  # ways for the processed prefix to have pairwise distinct uppercase letters

    for i, c in enumerate(S):
        if c == '?':
            low_ways = 26
        elif 'A' <= c <= 'Z':
            low_ways = 0
        else:
            low_ways = 1

        # Let i be the last lowercase character which has an uppercase character
        # after it. Then the prefix before i must have distinct uppercase letters,
        # S[i] must be lowercase, and the suffix must be U+ L*.
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
