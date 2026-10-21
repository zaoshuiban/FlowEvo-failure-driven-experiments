import sys

MOD = 998244353


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    N = int(data[0])

    # Modular inverses of 1..N
    inv = [0] * (N + 1)
    inv[1] = 1
    for i in range(2, N + 1):
        inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD

    # N!
    fact = 1
    for i in range(2, N + 1):
        fact = fact * i % MOD

    # Group numbers by digit length.
    # For a number with d digits, w = 10^d, and the linear factor is
    # (1-t) + wt = 1 + (10^d - 1)t.
    groups = []
    low = 1
    pow10 = 10
    while low <= N:
        end = min(N, pow10 - 1)
        count = end - low + 1
        sum_values = ((low + end) * count // 2) % MOD
        a = (pow10 - 1) % MOD
        groups.append((a, count, sum_values))
        low = pow10
        pow10 *= 10

    K = len(groups)

    # D(t) = product over groups (1 + a_i t)
    D = [1]
    for a, count, _ in groups:
        newD = [0] * (len(D) + 1)
        for i, val in enumerate(D):
            newD[i] = (newD[i] + val) % MOD
            newD[i + 1] = (newD[i + 1] + val * a) % MOD
        D = newD

    # R(t) = sum_i count_i * a_i * product_{j != i} (1 + a_j t)
    R = [0] * K
    for idx in range(K):
        a_i, count_i, _ = groups[idx]

        poly = [1]
        for j in range(K):
            if j == idx:
                continue
            b = groups[j][0]
            new_poly = [0] * (len(poly) + 1)
            for i, val in enumerate(poly):
                new_poly[i] = (new_poly[i] + val) % MOD
                new_poly[i + 1] = (new_poly[i + 1] + val * b) % MOD
            poly = new_poly

        factor = count_i % MOD * a_i % MOD
        for i, val in enumerate(poly):
            R[i] = (R[i] + factor * val) % MOD

    # Compute coefficients of P(t) = product (1 + a_i t)^{count_i}
    # using D(t) P'(t) = R(t) P(t).
    p = [0] * (N + 1)
    p[0] = 1

    R_len = len(R)

    for n in range(N):
        rhs = 0

        max_r = min(R_len - 1, n)
        for j in range(max_r + 1):
            rhs += R[j] * p[n - j]

        max_d = min(K, n)
        for j in range(1, max_d + 1):
            rhs -= D[j] * (n - j + 1) * p[n - j + 1]

        rhs %= MOD
        p[n + 1] = rhs * inv[n + 1] % MOD

    total_factor = 0

    # For each digit-length group, divide P(t) by (1 + a t),
    # integrate the resulting polynomial from 0 to 1, and multiply
    # by the sum of numbers in that group.
    for a, _, sum_values in groups:
        q_prev = 1
        integral = 1  # coefficient q_0 divided by 1

        for k in range(1, N):
            q = (p[k] - a * q_prev) % MOD
            integral = (integral + q * inv[k + 1]) % MOD
            q_prev = q

        total_factor = (total_factor + sum_values * integral) % MOD

    answer = fact * total_factor % MOD
    print(answer)


if __name__ == "__main__":
    main()