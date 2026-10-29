import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    if set(parameters.keys()) != {'digits', 'max_length'}:
        raise ValueError('unexpected keys')
    digits = parameters['digits']
    max_length = parameters['max_length']
    if not isinstance(digits, list):
        raise ValueError('digits must be a list')
    if not isinstance(max_length, int) or isinstance(max_length, bool):
        raise ValueError('max_length must be an integer')
    if len(digits) < 1 or len(digits) > 10:
        raise ValueError('digits length out of range')
    seen = set()
    for d in digits:
        if not isinstance(d, int) or isinstance(d, bool):
            raise ValueError('digit must be integer')
        if d < 0 or d > 9:
            raise ValueError('digit out of range')
        if d in seen:
            raise ValueError('digits must be distinct')
        seen.add(d)
    if max_length < 1 or max_length > 4:
        raise ValueError('max_length out of range')
    if max_length > len(digits):
        raise ValueError('max_length exceeds number of digits')

    def is_prime(n):
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        d = 5
        while d * d <= n:
            if n % d == 0 or n % (d + 2) == 0:
                return False
            d += 6
        return True

    primes = set()
    n = len(digits)
    for k in range(1, max_length + 1):
        for perm in _permutations(digits, k):
            if perm[0] == 0:
                continue
            val = 0
            for x in perm:
                val = val * 10 + x
            if is_prime(val):
                primes.add(val)
    return str(len(primes))

def _permutations(items, k):
    n = len(items)
    if k == 0:
        yield ()
        return
    if k > n:
        return
    indices = list(range(n))
    def rec(chosen, used):
        if len(chosen) == k:
            yield tuple(items[i] for i in chosen)
            return
        for i in range(n):
            if not (used >> i) & 1:
                chosen.append(i)
                yield from rec(chosen, used | (1 << i))
                chosen.pop()
    yield from rec([], 0)
