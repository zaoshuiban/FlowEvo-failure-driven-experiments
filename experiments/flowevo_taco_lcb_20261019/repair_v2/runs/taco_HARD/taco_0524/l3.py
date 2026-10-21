import sys

MOD = 1_000_000_007


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    m = data[0]
    a = data[1:1 + m]
    b = data[1 + m:1 + m + (m - 1)]

    if not any(b):
        print(0)
        return

    a.sort()
    v = a[-1]

    # H[x] = 1 + 1/2 + ... + 1/x modulo MOD, H[0] = 0
    H = [0] * (v + 1)
    if v >= 1:
        inv = [0] * (v + 1)
        inv[1] = 1
        H[1] = 1

        for i in range(2, v + 1):
            inv_i = MOD - (MOD // i) * inv[MOD % i] % MOD
            inv[i] = inv_i
            H[i] = (H[i - 1] + inv_i) % MOD

    selected = bytearray(v + 1)
    for x in a:
        selected[x] = 1

    complement = [i for i in range(v + 1) if not selected[i]]

    fact = [1] * (v + 1)
    for i in range(1, v + 1):
        fact[i] = fact[i - 1] * i % MOD

    invfact = [1] * (v + 1)
    invfact[v] = pow(fact[v], MOD - 2, MOD)
    for i in range(v, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    b_rev = b[::-1]
    ans = 0

    for x in a:
        hx = H[x]
        if hx == 0:
            continue

        # Evaluate P(-x)
        xx = (-x) % MOD
        value = 0
        for coeff in b_rev:
            value = (value * xx + coeff) % MOD

        # Product over complement: prod (y - x)
        prod = 1
        for y in complement:
            prod = prod * (y - x) % MOD

        inv_factor = invfact[x] * invfact[v - x] % MOD
        if x & 1:
            inv_factor = (-inv_factor) % MOD

        coefficient = value * prod % MOD * inv_factor % MOD
        ans = (ans - coefficient * hx) % MOD

    print(ans % MOD)


if __name__ == "__main__":
    main()