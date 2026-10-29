import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['multiplier', 'addend', 'seed', 'depth']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
    for key in parameters:
        if key not in required:
            raise ValueError('unexpected parameter: ' + key)
    a = parameters['multiplier']
    b = parameters['addend']
    c = parameters['seed']
    n = parameters['depth']
    for name, val in (('multiplier', a), ('addend', b), ('seed', c), ('depth', n)):
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(name + ' must be an integer')
    if n < 0:
        raise ValueError('depth must be nonnegative')
    if n > 100000:
        raise ValueError('depth too large')
    if abs(a) > 10**6 or abs(b) > 10**6 or abs(c) > 10**6:
        raise ValueError('parameter magnitude too large')
    x = c
    for _ in range(n):
        x = a * (b + x)
        if abs(x) > 10**100000:
            raise ValueError('result too large')
    return str(x)
