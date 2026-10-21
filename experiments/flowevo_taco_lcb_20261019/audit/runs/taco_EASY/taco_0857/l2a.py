from math import isqrt

_COUNTS = None


def _build_counts(max_c):
    counts = [0] * (max_c + 1)
    isqrt_ = isqrt

    for c in range(1, max_c + 1):
        n = c * c * c
        limit = isqrt_(n // 2)
        cnt = 0

        for a in range(1, limit + 1):
            b2 = n - a * a
            b = isqrt_(b2)
            if b * b == b2:
                cnt += 1

        counts[c] = cnt

    return counts


def find_abc_sumsqcube(c_max, num_sol):
    global _COUNTS

    if _COUNTS is None or c_max >= len(_COUNTS):
        _COUNTS = _build_counts(max(1000, c_max))

    return [
        c for c in range(1, c_max + 1)
        if _COUNTS[c] == num_sol
    ]