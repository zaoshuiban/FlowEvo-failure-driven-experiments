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

    deg = len(b) - 1  # m - 2
    ans = 0

    # complement size in [0, v]
    complement_size = v + 1 - m

    if complement_size < m - 1:
        selected = [False] * (v + 1)
        for x in a:
            selected[x] = True

        complement = [i for i in range(v + 1) if not selected[i]]

        fact = [1] * (v + 1)
        for i in range(1, v + 1):
            fact[i] = fact[i - 1] * i % MOD

        invfact = [1] * (v + 1)
        invfact[v] = pow(fact[v], MOD - 2, MOD)
        for i in range(v, 0, -1):
            invfact[i - 1] = invfact[i] * i % MOD

        for x in a:
            hx = H[x]
            if hx == 0:
                continue

            # Evaluate P(-x)
            xx = MOD - x
            val = b[deg]
            for k in range(deg - 1, -1, -1):
                val = (val * xx + b[k]) % MOD

            # Product over complement of (y - x)
            cp = 1
            for y in complement:
                cp = cp * (y - x) % MOD

            inv_full = invfact[x] * invfact[v - x] % MOD
            if x & 1:
                inv_full = (-inv_full) % MOD

            c = val * cp % MOD * inv_full % MOD
            ans = (ans - c * hx) % MOD

    else:
        for i, x in enumerate(a):
            hx = H[x]
            if hx == 0:
                continue

            # Evaluate P(-x)
            xx = MOD - x
            val = b[deg]
            for k in range(deg - 1, -1, -1):
                val = (val * xx + b[k]) % MOD

            d = 1

            # Product over previous elements
            for j in range(i):
                d = d * (x - a[j]) % MOD

            # Product over following elements
            for j in range(i + 1, m):
                d = d * (a[j] - x) % MOD

            # Correct the sign of the denominator
            if i & 1:
                d = (-d) % MOD

            c = val * pow(d, MOD - 2, MOD) % MOD
            ans = (ans - c * hx) % MOD

    print(ans % MOD)


if __name__ == "__main__":
    main()