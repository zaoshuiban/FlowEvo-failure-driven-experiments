import math


def _is_prime(n):
    if n < 2:
        return False

    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small_primes:
        if n % p == 0:
            return n == p

    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    # Deterministic Miller-Rabin bases for 64-bit integers,
    # plus extra bases for larger inputs.
    bases = (
        2, 325, 9375, 28178, 450775, 9780504, 1795265022,
        3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47
    )

    for a in bases:
        if a % n == 0:
            continue

        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue

        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False

    return True


def _pollard_rho(n):
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3

    for p in (5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return p

    c = 1
    while True:
        x = 2
        y = 2
        d = 1

        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)

        if d != n:
            return d

        c += 1


def _factor(n, factors):
    if n == 1:
        return

    if _is_prime(n):
        factors.add(n)
        return

    divisor = _pollard_rho(n)
    _factor(divisor, factors)
    _factor(n // divisor, factors)


def proper_fractions(n):
    if n <= 1:
        return 0

    factors = set()
    _factor(n, factors)

    result = n
    for prime in factors:
        result -= result // prime

    return result