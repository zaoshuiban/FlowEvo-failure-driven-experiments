from math import isqrt

def triangular_sum(n: int) -> bool:
    # Find the index t such that n = t * (t + 1) / 2
    d = 1 + 8 * n
    root = isqrt(d)

    if root * root != d:
        return False

    if (root - 1) % 2 != 0:
        return False

    t = (root - 1) // 2

    # n can be written as T_{m^2} = T_{m-1}^2 + T_m^2
    m = isqrt(t)
    return m >= 2 and m * m == t