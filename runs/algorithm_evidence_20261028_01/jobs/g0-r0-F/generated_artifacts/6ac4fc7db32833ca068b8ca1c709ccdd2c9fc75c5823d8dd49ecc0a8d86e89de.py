import itertools

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    digits = parameters.get('digits')
    max_length = parameters.get('max_length')
    if not isinstance(digits, list) or not digits:
        raise ValueError('digits must be a nonempty list')
    if len(digits) > 10:
        raise ValueError('too many digits')
    seen = set()
    for d in digits:
        if isinstance(d, bool) or not isinstance(d, int):
            raise ValueError('digits must be integers')
        if d < 0 or d > 9:
            raise ValueError('digit out of range')
        if d in seen:
            raise ValueError('digits must be distinct')
        seen.add(d)
    if isinstance(max_length, bool) or not isinstance(max_length, int):
        raise ValueError('max_length must be an integer')
    if max_length < 1 or max_length > 4:
        raise ValueError('max_length out of range')
    L = min(max_length, len(digits))
    primes = set()
    for k in range(1, L + 1):
        for tup in itertools.permutations(digits, k):
            if k > 1 and tup[0] == 0:
                continue
            n = 0
            for d in tup:
                n = n * 10 + d
            if n < 2:
                continue
            if k == 1:
                if n in (2, 3, 5, 7):
                    primes.add(n)
                continue
            last = tup[-1]
            if last not in (1, 3, 7, 9):
                continue
            if sum(tup) % 3 == 0:
                continue
            is_p = True
            d = 2
            while d * d <= n:
                if n % d == 0:
                    is_p = False
                    break
                d += 1
            if is_p:
                primes.add(n)
    return str(len(primes))