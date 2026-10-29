import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    if 'limit' not in parameters:
        raise ValueError('missing limit')
    limit = parameters['limit']
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError('limit must be an integer')
    if limit < 2:
        raise ValueError('limit must be at least 2')
    if limit > 10000000:
        raise ValueError('limit too large')
    n = limit - 1
    while n >= 1:
        s = 0
        m = n
        while m > 0:
            s += m % 10
            m //= 10
        if s == bin(n).count('1'):
            return str(n)
        n -= 1
    raise ValueError('no solution found')
