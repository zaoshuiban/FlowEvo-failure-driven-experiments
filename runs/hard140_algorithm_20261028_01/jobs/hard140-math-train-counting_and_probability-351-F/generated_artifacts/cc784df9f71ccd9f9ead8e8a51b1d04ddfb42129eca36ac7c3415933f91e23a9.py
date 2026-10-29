import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['target_x', 'target_y', 'max_steps']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
    tx = parameters['target_x']
    ty = parameters['target_y']
    N = parameters['max_steps']
    for v in (tx, ty, N):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError('parameters must be integers')
    if N < 0:
        raise ValueError('max_steps must be nonnegative')
    if N > 200:
        raise ValueError('max_steps too large')
    if abs(tx) > N or abs(ty) > N:
        raise ValueError('target out of reachable range')

    def count_walks(k, x, y):
        total = 0
        for a in range(k + 1):
            b = a - x
            if b < 0:
                continue
            for c in range(k - a - b + 1):
                d = c - y
                if d < 0:
                    continue
                if a + b + c + d != k:
                    continue
                total += math.factorial(k) // (math.factorial(a) * math.factorial(b) * math.factorial(c) * math.factorial(d))
        return total

    favorable = 0
    for k in range(N + 1):
        if (k - tx - ty) % 2 != 0:
            continue
        favorable += count_walks(k, tx, ty)

    total = 0
    for k in range(N + 1):
        total += 4 ** k

    if favorable == 0:
        return '0'

    g = math.gcd(favorable, total)
    m = favorable // g
    n = total // g
    return str(m + n)
