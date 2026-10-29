import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    if set(parameters.keys()) != {'digits', 'max_length'}:
        raise ValueError('unexpected keys')
    digits = parameters['digits']
    L = parameters['max_length']
    if not isinstance(digits, list) or not (1 <= len(digits) <= 10):
        raise ValueError('digits must be a list of 1..10 items')
    seen = set()
    for d in digits:
        if isinstance(d, bool) or not isinstance(d, int):
            raise ValueError('digits must be integers')
        if d < 0 or d > 9:
            raise ValueError('digit out of range')
        if d in seen:
            raise ValueError('digits must be distinct')
        seen.add(d)
    if isinstance(L, bool) or not isinstance(L, int):
        raise ValueError('max_length must be an integer')
    if L < 1 or L > 4:
        raise ValueError('max_length out of range')
    if L > len(digits):
        raise ValueError('max_length exceeds number of digits')

    def is_prime(n):
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0:
            return False
        r = int(math.isqrt(n))
        f = 3
        while f <= r:
            if n % f == 0:
                return False
            f += 2
        return True

    count = 0
    used = [False] * len(digits)

    def rec(length, value, start_zero):
        nonlocal count
        if length > 0:
            if is_prime(value):
                count += 1
        if length == L:
            return
        for i in range(len(digits)):
            if used[i]:
                continue
            d = digits[i]
            if length == 0 and d == 0:
                continue
            used[i] = True
            rec(length + 1, value * 10 + d, False)
            used[i] = False

    rec(0, 0, True)
    return str(count)
