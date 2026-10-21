from fractions import Fraction
from math import gcd

def expand(x, digit):
    if isinstance(x, float):
        x = Fraction(str(x))
    else:
        x = Fraction(x)

    p, q = x.numerator, x.denominator

    if digit <= 1 or p == 0:
        return [1, 1]

    limit = 10 ** (digit - 1)

    # S_n = N / D, where D = q^n * n!
    N, D = 1, 1
    n = 1
    p_pow = p

    while True:
        factor = q * n
        D *= factor
        N = N * factor + p_pow

        g = gcd(abs(N), D)
        if abs(N) // g >= limit:
            return [N // g, D // g]

        n += 1
        p_pow *= p