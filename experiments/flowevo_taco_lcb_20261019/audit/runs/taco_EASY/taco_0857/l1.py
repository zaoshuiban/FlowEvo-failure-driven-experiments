from math import isqrt

_counts = None

def _build_counts(limit):
    counts = [0] * (limit + 1)
    for c in range(1, limit + 1):
        n = c * c * c
        count = 0
        max_a = isqrt(n // 2)

        for a in range(1, max_a + 1):
            rem = n - a * a
            b = isqrt(rem)
            if b * b == rem:
                count += 1

        counts[c] = count

    return counts


def find_abc_sumsqcube(c_max, num_sol):
    global _counts

    if _counts is None:
        _counts = _build_counts(max(1000, c_max))
    elif c_max >= len(_counts):
        _counts = _build_counts(c_max)

    return [c for c in range(1, c_max + 1) if _counts[c] == num_sol]