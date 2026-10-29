import itertools

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    if set(parameters.keys()) != {'digits', 'max_length'}:
        raise ValueError('unexpected keys')
    digits = parameters['digits']
    max_length = parameters['max_length']
    if not isinstance(digits, list) or not (1 <= len(digits) <= 10):
        raise ValueError('digits must be a list of length 1..10')
    seen = set()
    for d in digits:
        if isinstance(d, bool) or not isinstance(d, int):
            raise ValueError('digits must be integers')
        if d < 0 or d > 9:
            raise ValueError('digits out of range')
        if d in seen:
            raise ValueError('digits must be distinct')
        seen.add(d)
    if isinstance(max_length, bool) or not isinstance(max_length, int):
        raise ValueError('max_length must be an integer')
    if max_length < 1 or max_length > 4:
        raise ValueError('max_length out of range')
    if max_length > len(digits):
        raise ValueError('max_length exceeds number of distinct digits')

    def is_prime(v):
        if v < 2:
            return False
        if v < 4:
            return True
        if v % 2 == 0 or v % 3 == 0:
            return False
        d = 5
        while d * d <= v:
            if v % d == 0 or v % (d + 2) == 0:
                return False
            d += 6
        return True

    primes = set()
    for k in range(1, max_length + 1):
        for perm in itertools.permutations(digits, k):
            if k >= 2 and perm[0] == 0:
                continue
            v = 0
            for x in perm:
                v = v * 10 + x
            if is_prime(v):
                primes.add(v)
    return str(len(primes))