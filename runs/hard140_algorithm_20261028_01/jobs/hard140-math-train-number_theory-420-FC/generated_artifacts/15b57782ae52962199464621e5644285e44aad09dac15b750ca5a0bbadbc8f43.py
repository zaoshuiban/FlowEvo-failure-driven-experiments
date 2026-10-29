def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    if 'upper_bound' not in parameters:
        raise ValueError('missing upper_bound')
    n = parameters['upper_bound']
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError('upper_bound must be an integer')
    if n < 2:
        raise ValueError('upper_bound must be at least 2')
    if n > 10000000:
        raise ValueError('upper_bound too large')
    for x in range(n - 1, 0, -1):
        s = 0
        y = x
        while y > 0:
            s += y % 10
            y //= 10
        p = 0
        y = x
        while y > 0:
            p += y & 1
            y >>= 1
        if s == p:
            return str(x)
    raise ValueError('no solution found')
