from math import isqrt

_counts = []
_computed_to = 0


def _ensure_counts(c_max):
    global _counts, _computed_to

    if c_max <= _computed_to:
        return

    if len(_counts) <= c_max:
        _counts.extend([0] * (c_max + 1 - len(_counts)))

    for c in range(_computed_to + 1, c_max + 1):
        n = c * c * c
        count = 0
        limit = isqrt(n // 2)

        for a in range(1, limit + 1):
            b2 = n - a * a
            b = isqrt(b2)
            if b * b == b2:
                count += 1

        _counts[c] = count

    _computed_to = c_max


def find_abc_sumsqcube(c_max, num_sol):
    _ensure_counts(c_max)
    return [c for c in range(1, c_max + 1) if _counts[c] == num_sol]