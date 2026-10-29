import math

def _digit_sum(n, base):
    if n < 0:
        raise ValueError("negative values not supported")
    if base < 2:
        raise ValueError("base must be at least 2")
    total = 0
    while n > 0:
        total += n % base
        n //= base
    return total

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be a dict")
    lo = parameters.get("lo")
    hi = parameters.get("hi")
    base_a = parameters.get("base_a", 10)
    base_b = parameters.get("base_b", 2)
    none_sentinel = parameters.get("none_sentinel", -1)
    for name, val in (("lo", lo), ("hi", hi), ("base_a", base_a), ("base_b", base_b), ("none_sentinel", none_sentinel)):
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(name + " must be an integer")
    if base_a < 2 or base_b < 2:
        raise ValueError("bases must be at least 2")
    if lo < 0:
        raise ValueError("lo must be nonnegative")
    if hi < lo:
        raise ValueError("hi must be at least lo")
    if hi - lo > 2000000:
        raise ValueError("range too large")
    best = None
    for n in range(lo, hi):
        if _digit_sum(n, base_a) == _digit_sum(n, base_b):
            best = n
    if best is None:
        return str(none_sentinel)
    return str(best)