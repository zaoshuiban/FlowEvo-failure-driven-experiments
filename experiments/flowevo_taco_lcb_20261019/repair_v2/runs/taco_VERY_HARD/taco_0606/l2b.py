import sys


def factorize(m):
    factors = []
    d = 2
    while d * d <= m:
        if m % d == 0:
            p = d
            pk = 1
            while m % d == 0:
                m //= d
                pk *= d
            factors.append((p, pk))
        d += 1
    if m > 1:
        factors.append((m, m))
    return factors


def vp_fact(n, p):
    result = 0
    while n:
        n //= p
        result += n
    return result


def factorial_without_p(n, p, pk, f):
    result = 1
    block_product = f[pk]

    while n > 0:
        result = result * pow(block_product, n // pk, pk) % pk
        result = result * f[n % pk] % pk
        n //= p

    return result


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
    current_mod = 1

    for p, pk in factors:
        a = 0
        temp = pk
        while temp % p == 0:
            a += 1
            temp //= p

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
                    prod = prod * i % pk
                f[i] = prod

            un = factorial_without_p(n, p, pk, f)
            uk = factorial_without_p(k, p, pk, f)
            unk = factorial_without_p(n - k, p, pk, f)

            residue = un * pow(uk, -1, pk) % pk
            residue = residue * pow(unk, -1, pk) % pk
            residue = residue * pow(p, exponent, pk) % pk

        if current_mod == 1:
            x = residue % pk
            current_mod = pk
        else:
            diff = (residue - x) % pk
            inv = pow(current_mod % pk, -1, pk)
            t = diff * inv % pk

            x += current_mod * t
            current_mod *= pk
            x %= current_mod

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