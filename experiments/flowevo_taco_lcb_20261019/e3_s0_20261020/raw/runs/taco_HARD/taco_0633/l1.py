import sys

MOD = 10**9 + 7

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    cases = []
    max_k = 0

    for _ in range(t):
        k = data[idx]
        n = data[idx + 1]
        r = data[idx + 2]
        idx += 3
        cases.append((k, n, r))
        max_k = max(max_k, k)

    inv = [0] * (max_k + 2)
    inv[1] = 1
    for i in range(2, max_k + 2):
        inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD

    answers = []

    for k, n, r_input in cases:
        r = r_input % MOD
        inv_den = pow((r - 1) % MOD, MOD - 2, MOD)

        r_pow_n1 = pow(r, n + 1, MOD)
        n1 = (n + 1) % MOD

        s = [0] * (k + 1)
        base_power = 1

        for m in range(k + 1):
            a = (r_pow_n1 * base_power - r) % MOD

            total = 0
            if m > 0:
                comb = 1
                for j in range(m):
                    total = (total + comb * s[j]) % MOD
                    comb = comb * (m - j) % MOD * inv[j + 1] % MOD

            s[m] = (a - r * total) % MOD * inv_den % MOD
            base_power = base_power * n1 % MOD

        answers.append(str(s[k]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()