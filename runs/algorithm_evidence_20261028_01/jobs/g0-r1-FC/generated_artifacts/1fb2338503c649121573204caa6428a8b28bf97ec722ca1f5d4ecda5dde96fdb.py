import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('DECLINED')
    digits = parameters.get('digits')
    max_length = parameters.get('max_length')
    if not isinstance(digits, list) or not isinstance(max_length, int) or isinstance(max_length, bool):
        raise ValueError('DECLINED')
    if len(digits) < 1 or len(digits) > 10:
        raise ValueError('DECLINED')
    seen = set()
    for d in digits:
        if not isinstance(d, int) or isinstance(d, bool) or d < 0 or d > 9:
            raise ValueError('DECLINED')
        if d in seen:
            raise ValueError('DECLINED')
        seen.add(d)
    if max_length < 1 or max_length > 4:
        raise ValueError('DECLINED')
    if max_length > len(digits):
        raise ValueError('DECLINED')
    ds = sorted(seen)
    n = len(ds)

    def is_prime(x):
        if x < 2:
            return False
        if x < 4:
            return True
        if x % 2 == 0 or x % 3 == 0:
            return False
        d = 5
        while d * d <= x:
            if x % d == 0 or x % (d + 2) == 0:
                return False
            d += 6
        return True

    primes = set()
    for k in range(1, max_length + 1):
        for perm in _permutations(ds, k):
            if perm[0] == 0:
                continue
            val = 0
            for dgt in perm:
                val = val * 10 + dgt
            if is_prime(val):
                primes.add(val)
    return str(len(primes))

def _permutations(items, k):
    if k == 0:
        yield ()
        return
    for i in range(len(items)):
        rest = items[:i] + items[i+1:]
        for tail in _permutations(rest, k - 1):
            yield (items[i],) + tail
