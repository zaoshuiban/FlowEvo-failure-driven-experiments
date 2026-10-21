import sys


def factorize(m):
    factors = []

    if m % 2 == 0:
        a = 0
        pk = 1
        while m % 2 == 0:
            m //= 2
            a += 1
            pk *= 2
        factors.append((2, a, pk))

    d = 3
    while d * d <= m:
        if m % d == 0:
            a = 0
            pk = 1
            while m % d == 0:
                m //= d
                a += 1
                pk *= d
            factors.append((d, a, pk))
        d += 2

    if m > 1:
        factors.append((m, 1, m))

    return factors


def vp_fact(n, p):
    result = 0
    while n:
        n //= p
        result += n
    return result


def comb_mod_prime_power(n, k, p, a, pk):
    if pk == 1:
        return 0

    e = vp_fact(n, p) - vp_fact(k, p) - vp_fact(n - k, p)
    if e >= a:
        return 0

    # f[i] = product of numbers <= i that are not divisible by p, modulo pk
    f = [1] * (pk + 1)
    prod = 1
    for i in range(1, pk + 1):
        if i % p != 0:
            prod = (prod * i) % pk
        f[i] = prod

    def factorial_without_p(x):
        res = 1
        while x:
            res = (res * pow(f[pk], x // pk, pk)) % pk
            res = (res * f[x % pk]) % pk
            x //= p
        return res

    num = factorial_without_p(n)
    den = factorial_without_p(k) * factorial_without_p(n - k) % pk

    res = num * pow(den, -1, pk) % pk
    res = res * pow(p, e, pk) % pk
    return res


def comb_mod(n, k, mod):
    if k < 0 or k > n:
        return 0
    if mod == 1:
        return 0

    k = min(k, n - k)
    if k == 0:
        return 1 % mod

    factors = factorize(mod)
    residues = []

    for p, a, pk in factors:
        residues.append((comb_mod_prime_power(n, k, p, a, pk), pk))

    # Chinese Remainder Theorem
    x = 0
    current = 1

    for r, mi in residues:
        inv = pow(current % mi, -1, mi)
        t = ((r - x) % mi) * inv % mi
        x += current * t
        current *= mi
        x %= current

    return x % mod


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n_len = data[idx]
        k_len = data[idx + 1]
        mod = data[idx + 2]
        idx += 3

        pieces = (n_len + k_len - 1) // k_len
        deficit = pieces * k_len - n_len

        total = pieces + deficit - 1
        ways = comb_mod(total, deficit, mod)

        answers.append(f"{pieces} {ways}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()