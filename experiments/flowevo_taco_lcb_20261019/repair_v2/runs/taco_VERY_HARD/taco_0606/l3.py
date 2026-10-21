import sys


def factorize(m):
    factors = []
    p = 2
    while p * p <= m:
        if m % p == 0:
            pk = 1
            exp = 0
            while m % p == 0:
                m //= p
                pk *= p
                exp += 1
            factors.append((p, pk, exp))
        p += 1
    if m > 1:
        factors.append((m, m, 1))
    return factors


def vp_fact(n, p):
    res = 0
    while n:
        n //= p
        res += n
    return res


def inv_mod(a, mod):
    # Extended Euclidean algorithm; assumes gcd(a, mod) = 1
    b = mod
    x0, x1 = 1, 0
    while b:
        q = a // b
        a, b = b, a - q * b
        x0, x1 = x1, x0 - q * x1
    return x0 % mod


def fact_without_p(n, p, pk, f, block_product):
    # n! with all factors p removed, modulo pk = p^a
    res = 1
    while n > 0:
        res = (res * pow(block_product, n // pk, pk)) % pk
        res = (res * f[n % pk]) % pk
        n //= p
    return res


def binom_mod(n, k, mod):
    if mod == 1:
        return 0

    if k < 0 or k > n:
        return 0

    if k == 0 or k == n:
        return 1 % mod

    k = min(k, n - k)
    if k == 0:
        return 1 % mod

    factors = factorize(mod)

    x = 0
    cur_mod = 1

    for p, pk, a in factors:
        exponent = (
            vp_fact(n, p)
            - vp_fact(k, p)
            - vp_fact(n - k, p)
        )

        if exponent >= a:
            residue = 0
        else:
            f = [1] * (pk + 1)
            prod = 1

            for i in range(1, pk + 1):
                if i % p != 0:
                    prod = (prod * i) % pk
                f[i] = prod

            block_product = f[pk]

            un = fact_without_p(n, p, pk, f, block_product)
            uk = fact_without_p(k, p, pk, f, block_product)
            unk = fact_without_p(n - k, p, pk, f, block_product)

            residue = un * inv_mod(uk, pk) % pk
            residue = residue * inv_mod(unk, pk) % pk
            residue = residue * pow(p, exponent, pk) % pk

        # CRT merge
        diff = (residue - x) % pk
        inv = inv_mod(cur_mod % pk, pk)
        t = diff * inv % pk

        x += cur_mod * t
        cur_mod *= pk
        x %= cur_mod

    return x % mod


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        mod = int(data[idx + 2])
        idx += 3

        pieces = (n + k - 1) // k
        deficit = pieces * k - n

        total = pieces + deficit - 1
        ways = binom_mod(total, deficit, mod)

        answers.append(f"{pieces} {ways}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()