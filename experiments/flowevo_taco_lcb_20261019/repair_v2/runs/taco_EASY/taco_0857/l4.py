from math import isqrt

_MAX_C = 1000
_COUNTS = [0] * (_MAX_C + 1)

for _c in range(1, _MAX_C + 1):
    _n = _c * _c * _c
    _count = 0
    _a = 1

    while 2 * _a * _a <= _n:
        _b2 = _n - _a * _a
        _b = isqrt(_b2)
        if _b * _b == _b2:
            _count += 1
        _a += 1

    _COUNTS[_c] = _count


def _extend_counts(c_max):
    global _MAX_C, _COUNTS

    if c_max <= _MAX_C:
        return

    _COUNTS.extend([0] * (c_max - _MAX_C))

    for c in range(_MAX_C + 1, c_max + 1):
        n = c * c * c
        count = 0
        a = 1

        while 2 * a * a <= n:
            b2 = n - a * a
            b = isqrt(b2)
            if b * b == b2:
                count += 1
            a += 1

        _COUNTS[c] = count

    _MAX_C = c_max


def find_abc_sumsqcube(c_max, num_sol):
    _extend_counts(c_max)

    return [
        c
        for c in range(1, c_max + 1)
        if _COUNTS[c] == num_sol
    ]