import math
from fractions import Fraction

def _cbrt(x):
    if x < 0:
        return -((-x) ** (1.0 / 3.0))
    return x ** (1.0 / 3.0)

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['p', 'q', 'multiplier', 'bound', 'tolerance']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
    p = parameters['p']
    q = parameters['q']
    m = parameters['multiplier']
    bound = parameters['bound']
    tol = parameters['tolerance']
    for name, val in [('p', p), ('q', q), ('multiplier', m), ('bound', bound)]:
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(name + ' must be an integer')
        if val < 1:
            raise ValueError(name + ' must be positive')
    if isinstance(tol, bool) or not isinstance(tol, (int, float)):
        raise ValueError('tolerance must be a number')
    if tol <= 0:
        raise ValueError('tolerance must be positive')
    if bound > 200:
        raise ValueError('bound too large')
    if p == q:
        raise ValueError('p and q must differ')
    inner = _cbrt(p) - _cbrt(q)
    if inner <= 0:
        raise ValueError('p must exceed q for a real square root')
    target = m * math.sqrt(inner)
    best = None
    for a in range(1, bound + 1):
        ca = _cbrt(a)
        for b in range(1, bound + 1):
            cb = _cbrt(b)
            partial = ca + cb
            for c in range(1, bound + 1):
                val = partial - _cbrt(c)
                if abs(val - target) < tol:
                    s = a + b + c
                    if best is None or s < best:
                        best = s
    if best is None:
        raise ValueError('no solution found within bound')
    return str(best)