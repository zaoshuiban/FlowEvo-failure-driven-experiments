import math

_counts = [0]
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
        a = 1

        # We need a <= b, so a^2 + b^2 >= 2a^2.
        while 2 * a * a <= n:
            b2 = n - a * a
            b = math.isqrt(b2)
            if b * b == b2:
                count += 1
            a += 1

        _counts[c] = count

    _computed_to = c_max


def find_abc_sumsqcube(c_max, num_sol):
    _ensure_counts(c_max)
    return [
        c for c in range(1, c_max + 1)
        if _counts[c] == num_sol
    ]