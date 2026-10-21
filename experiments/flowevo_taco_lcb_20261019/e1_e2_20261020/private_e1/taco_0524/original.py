import sys

MOD = 1_000_000_007


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    m = data[0]
    a = data[1:1 + m]
    b = data[1 + m:1 + m + (m - 1)]

    v = max(a)

    # H[i] = 1 + 1/2 + ... + 1/i modulo MOD
    H = [0] * (v + 1)
    if v >= 1:
        inv = [0] * (v + 1)
        inv[1] = 1
        H[1] = 1

        for i in range(2, v + 1):
            inv_i = MOD - (MOD // i) * inv[MOD % i] % MOD
            inv[i] = inv_i
            H[i] = (H[i - 1] + inv_i) % MOD

    # Factorials and inverse factorials
    fact = [1] * (v + 1)
    for i in range(1, v + 1):
        fact[i] = fact[i - 1] * i % MOD

    invfact = [1] * (v + 1)
    invfact[v] = pow(fact[v], MOD - 2, MOD)
    for i in range(v, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    selected = bytearray(v + 1)
    for x in a:
        selected[x] = 1

    complement = [i for i in range(v + 1) if not selected[i]]

    b_rev = b[::-1]

    ans = 0

    for x in a:
        # Evaluate P(-x)
        neg_x = 0 if x == 0 else MOD - x
        value = 0
        for coeff in b_rev:
            value = (value * neg_x + coeff) % MOD

        if value == 0:
            continue

        # T(x) = product over y not in A of (x - y)
        product = 1
        for y in complement:
            product = product * (x - y) % MOD

        coeff = value * product % MOD
        coeff = coeff * invfact[x] % MOD
        coeff = coeff * invfact[v - x] % MOD

        if (m - 1 + v - x) & 1:
            coeff = (-coeff) % MOD

        ans = (ans - coeff * H[x]) % MOD

    print(ans % MOD)


if __name__ == "__main__":
    main()