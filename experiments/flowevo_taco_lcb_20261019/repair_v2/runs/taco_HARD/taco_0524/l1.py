import sys

MOD = 1_000_000_007
MAXV = 5000


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    m = data[0]
    A = data[1:1 + m]
    B = data[1 + m:1 + m + (m - 1)]

    # Factorials and inverse factorials
    fact = [1] * (MAXV + 1)
    for i in range(1, MAXV + 1):
        fact[i] = fact[i - 1] * i % MOD

    invfact = [1] * (MAXV + 1)
    invfact[MAXV] = pow(fact[MAXV], MOD - 2, MOD)
    for i in range(MAXV, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    # Harmonic numbers H[a] = 1 + 1/2 + ... + 1/a
    max_a = max(A)
    H = [0] * (max_a + 1)

    if max_a >= 1:
        inv = [0] * (max_a + 1)
        inv[1] = 1
        H[1] = 1

        for i in range(2, max_a + 1):
            inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD
            H[i] = (H[i - 1] + inv[i]) % MOD

    present = bytearray(MAXV + 1)
    for a in A:
        present[a] = 1

    complement_size = MAXV + 1 - m
    direct = (m - 1 <= complement_size)

    if not direct:
        C = [i for i in range(MAXV + 1) if present[i] == 0]
    else:
        C = None

    rev_b = B[::-1]

    ans = 0

    for a in A:
        # Compute P(-a)
        if a == 0:
            p_value = B[0] % MOD
        else:
            p_value = 0
            for coeff in rev_b:
                p_value = (coeff - a * p_value) % MOD

        # Compute denominator:
        # D_i = product_{j != i} (a_j - a_i)
        if direct:
            d = 1
            for s in A:
                if s != a:
                    d = d * (s - a) % MOD

            inv_d = pow(d, MOD - 2, MOD)
        else:
            cp = 1
            for c in C:
                cp = cp * (c - a) % MOD

            # all_product = product_{s=0, s != a}^{5000} (s - a)
            # 1 / all_product = (-1)^a / (a! * (5000-a)!)
            inv_all = invfact[a] * invfact[MAXV - a] % MOD
            if a & 1:
                inv_all = (-inv_all) % MOD

            # D = all_product / cp, so 1 / D = cp / all_product
            inv_d = cp * inv_all % MOD

        term = p_value * inv_d % MOD
        term = term * H[a] % MOD

        ans = (ans - term) % MOD

    print(ans % MOD)


if __name__ == "__main__":
    main()