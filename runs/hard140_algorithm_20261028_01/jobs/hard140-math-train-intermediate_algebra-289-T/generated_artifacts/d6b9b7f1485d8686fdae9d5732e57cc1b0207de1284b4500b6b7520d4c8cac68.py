import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    plus = parameters.get('plus_points')
    minus = parameters.get('minus_points')
    a_positive = parameters.get('a_positive', True)
    if not isinstance(plus, list) or not isinstance(minus, list):
        raise ValueError('point sets must be lists')
    if not plus or not minus:
        raise ValueError('point sets must be nonempty')
    if not isinstance(a_positive, bool):
        raise ValueError('a_positive must be boolean')
    if not a_positive:
        raise ValueError('only positive a supported')
    for v in plus + minus:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError('points must be integers')
    if len(set(plus)) != len(plus) or len(set(minus)) != len(minus):
        raise ValueError('points must be distinct within each set')
    if set(plus) & set(minus):
        raise ValueError('point sets must be disjoint')
    if len(plus) > 12 or len(minus) > 12:
        raise ValueError('too many points')
    for v in plus + minus:
        if abs(v) > 10**6:
            raise ValueError('point magnitude too large')

    def lcm(a, b):
        return a // math.gcd(a, b) * b

    def product_at(roots, x):
        p = 1
        for r in roots:
            p *= (x - r)
        return p

    L = 1
    for b in minus:
        t = product_at(plus, b)
        if t == 0:
            raise ValueError('unexpected zero product')
        L = lcm(L, abs(t))

    base = L // math.gcd(L, 2)

    def divided_differences(xs, ys):
        n = len(xs)
        table = [[0] * n for _ in range(n)]
        for i in range(n):
            table[i][0] = ys[i]
        for j in range(1, n):
            for i in range(n - j):
                denom = xs[i + j] - xs[i]
                if denom == 0:
                    raise ValueError('duplicate x')
                num = table[i + 1][j - 1] - table[i][j - 1]
                if num % denom != 0:
                    return None
                table[i][j] = num // denom
        return [table[0][j] for j in range(n)]

    def construct_g(xs, ys):
        coeffs = divided_differences(xs, ys)
        if coeffs is None:
            return None
        poly = [0]
        for c in coeffs:
            new = [0] * (len(poly) + 1)
            for i, v in enumerate(poly):
                new[i] += v
                new[i + 1] -= v * xs[len(new) - 2] if False else 0
            poly = new
        return coeffs

    def newton_eval(xs, coeffs, x):
        n = len(coeffs)
        result = coeffs[n - 1]
        for i in range(n - 2, -1, -1):
            result = result * (x - xs[i]) + coeffs[i]
        return result

    def try_a(a):
        xs = sorted(minus)
        ys = []
        for b in xs:
            t = product_at(plus, b)
            num = -2 * a
            if num % t != 0:
                return False
            ys.append(num // t)
        coeffs = divided_differences(xs, ys)
        if coeffs is None:
            return False
        for b, y in zip(xs, ys):
            if newton_eval(xs, coeffs, b) != y:
                return False
        return True

    a = base
    limit = base * 1000
    while a <= limit:
        if try_a(a):
            return str(a)
        a += base
    raise ValueError('no solution found within bound')
