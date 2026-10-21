from math import isqrt

def triangular_sum(n):
    # Find the index m such that n = m * (m + 1) / 2
    discriminant = 8 * n + 1
    root = isqrt(discriminant)

    if root * root != discriminant:
        return False

    m = (root - 1) // 2

    # n must be a triangular number T_m, where m = (k + 1)^2 for some k >= 1.
    # Thus m must be a perfect square, and m >= 4.
    s = isqrt(m)
    return s * s == m and m >= 4