import sys

MOD = 1_000_000_007

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    m = data[0]
    a = data[1:1 + m]
    b = data[1 + m:1 + m + (m - 1)]

    # Remove zero high-degree coefficients.
    while b and b[-1] == 0:
        b.pop()

    if not b:
        print(0)
        return

    M = max(a)

    # Modular inverses and harmonic numbers H[i] = 1 + 1/2 + ... + 1/i.
    inv = [0] * (M + 1)
    H = [0] * (M + 1)

    if M >= 1:
        inv[1] = 1
        H[1] = 1
        for i in range(2, M + 1):
            inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD
            H[i] = (H[i - 1] + inv[i]) % MOD

    # Factorials up to M.
    fact = [1] * (M + 1)
    for i in range(1, M + 1):
        fact[i] = fact[i - 1] * i % MOD

    present = [False] * (M + 1)
    for x in a:
        present[x] = True

    absent = [i for i in range(M + 1) if not present[i]]

    # If most values are present, compute products of differences using
    # the full integer range and divide by the absent ones.
    use_absent = len(absent) < m

    rev = b[::-1]
    first = rev[0]
    tail = rev[1:]

    ans = 0

    for ai in a:
        # H[0] = 0, so a_i = 0 gives no contribution.
        if ai == 0:
            continue

        x = MOD - ai  # -ai modulo MOD

        # Evaluate P(-ai) by Horner's method.
        val = first
        for coeff in tail:
            val = (val * x + coeff) % MOD

        if val == 0:
            continue

        # D = product_{j != i} (a_j - a_i)
        if use_absent:
            D = fact[ai] * fact[M - ai] % MOD
            if ai & 1:
                D = (-D) % MOD

            prod_absent = 1
            for t in absent:
                prod_absent = prod_absent * (t - ai) % MOD

            D = D * pow(prod_absent, MOD - 2, MOD) % MOD
        else:
            D = 1
            for v in a:
                if v != ai:
                    D = D * (v - ai) % MOD

        c = val * pow(D, MOD - 2, MOD) % MOD

        # Sum = - sum_i c_i * H[a_i]
        ans = (ans - c * H[ai]) % MOD

    print(ans % MOD)


if __name__ == "__main__":
    main()