import sys
from array import array


def factorize(m):
    factors = []
    d = 2
    while d * d <= m:
        if m % d == 0:
            p = d
            pe = 1
            a = 0
            while m % d == 0:
                m //= d
                pe *= d
                a += 1
            factors.append((p, pe, a))
        d += 1 if d == 2 else 2

    if m > 1:
        factors.append((m, m, 1))

    return factors


def vp_fact(n, p):
    res = 0
    while n:
        n //= p
        res += n
    return res


def factorial_unit_mod(n, p, mod, prefix):
    res = 1
    block_product = prefix[mod]

    while n > 0:
        res = (res * pow(block_product, n // mod, mod)) % mod
        res = (res * prefix[n % mod]) % mod
        n //= p

    return res


def binom_mod_prime_power(n, k, p, mod, exponent):
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1 % mod

    e = vp_fact(n, p) - vp_fact(k, p) - vp_fact(n - k, p)
    if e >= exponent:
        return 0

    prefix = array('I', [1]) * (mod + 1)
    prod = 1
    for i in range(1, mod + 1):
        if i % p != 0:
            prod = (prod * i) % mod
        prefix[i] = prod

    fn = factorial_unit_mod(n, p, mod, prefix)
    fk = factorial_unit_mod(k, p, mod, prefix)
    fnk = factorial_unit_mod(n - k, p, mod, prefix)

    res = fn
    res = (res * pow(fk, -1, mod)) % mod
    res = (res * pow(fnk, -1, mod)) % mod
    res = (res * pow(p, e, mod)) % mod

    return res


def nCr_mod(n, r, mod):
    if r < 0 or r > n:
        return 0

    r = min(r, n - r)
    if r == 0:
        return 1 % mod

    factors = factorize(mod)
    residues = []

    for p, pe, exponent in factors:
        residues.append((binom_mod_prime_power(n, r, p, pe, exponent), pe))

    x = 0
    cur_mod = 1

    for rem, q in residues:
        diff = (rem - x) % q
        inv = pow(cur_mod % q, -1, q)
        t = (diff * inv) % q

        x += cur_mod * t
        cur_mod *= q
        x %= cur_mod

    return x % mod


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        m = data[idx + 2]
        idx += 3

        parts = (n + k - 1) // k
        deficit = parts * k - n

        total = deficit + parts - 1
        choose = min(deficit, parts - 1)

        ways = nCr_mod(total, choose, m)
        answers.append(f"{parts} {ways}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()