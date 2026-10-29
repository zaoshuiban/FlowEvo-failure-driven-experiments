import math
import fractions

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    if set(parameters.keys()) != {'nodes', 'signs'}:
        raise ValueError('parameters must have exactly nodes and signs')
    nodes = parameters['nodes']
    signs = parameters['signs']
    if not isinstance(nodes, list) or not isinstance(signs, list):
        raise ValueError('nodes and signs must be lists')
    if len(nodes) != len(signs):
        raise ValueError('nodes and signs must have same length')
    n = len(nodes)
    if n == 0:
        raise ValueError('nodes must be nonempty')
    if n > 40:
        raise ValueError('too many nodes')
    seen = set()
    for x in nodes:
        if isinstance(x, bool) or not isinstance(x, int):
            raise ValueError('nodes must be integers')
        if x in seen:
            raise ValueError('nodes must be distinct')
        seen.add(x)
        if abs(x) > 10**6:
            raise ValueError('node magnitude too large')
    for s in signs:
        if isinstance(s, bool) or not isinstance(s, int):
            raise ValueError('signs must be integers')
        if s not in (-1, 0, 1):
            raise ValueError('signs must be -1, 0, or 1')
    if all(s == 0 for s in signs):
        return '1'
    # Compute interpolation polynomial Q of degree < n with Q(nodes[i]) = signs[i]
    # using Lagrange interpolation with exact fractions.
    # Q(x) = sum_i signs[i] * prod_{j != i} (x - nodes[j]) / (nodes[i] - nodes[j])
    # Build coefficient list (ascending powers) as Fractions.
    coeffs = [fractions.Fraction(0) for _ in range(n)]
    for i in range(n):
        if signs[i] == 0:
            continue
        # numerator polynomial prod_{j != i} (x - nodes[j])
        num = [fractions.Fraction(1)]
        for j in range(n):
            if j == i:
                continue
            # multiply by (x - nodes[j])
            new = [fractions.Fraction(0) for _ in range(len(num) + 1)]
            for k in range(len(num)):
                new[k] += num[k] * (-nodes[j])
                new[k + 1] += num[k]
            num = new
        denom = 1
        for j in range(n):
            if j == i:
                continue
            denom *= (nodes[i] - nodes[j])
        factor = fractions.Fraction(signs[i], denom)
        for k in range(len(num)):
            coeffs[k] += num[k] * factor
    # LCM of denominators of coefficients
    lcm = 1
    for c in coeffs:
        d = c.denominator
        lcm = lcm * d // math.gcd(lcm, d)
    return str(lcm)
