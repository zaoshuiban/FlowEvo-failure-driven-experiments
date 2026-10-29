import math
from fractions import Fraction

def _lcm(a, b):
    return a // math.gcd(a, b) * b

def _crt_pair(r1, m1, r2, m2):
    g = math.gcd(m1, m2)
    if (r2 - r1) % g != 0:
        return None
    m1g = m1 // g
    m2g = m2 // g
    diff = (r2 - r1) // g
    inv = pow(m1g % m2g, -1, m2g) if m2g > 1 else 0
    t = (diff * inv) % m2g
    r = r1 + m1 * t
    m = m1 * m2g
    r %= m
    return (r, m)

def _solve_congruences(congs):
    r, m = 0, 1
    for (ri, mi) in congs:
        if mi == 0:
            continue
        mi = abs(mi)
        res = _crt_pair(r, m, ri % mi, mi)
        if res is None:
            return None
        r, m = res
    return (r, m)

def _interp_integer(pts):
    n = len(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    coef = [Fraction(0) for _ in range(n)]
    for i in range(n):
        num = [Fraction(1)]
        den = 1
        for j in range(n):
            if j == i:
                continue
            newnum = [Fraction(0)] * (len(num) + 1)
            for k in range(len(num)):
                newnum[k] -= num[k] * xs[j]
                newnum[k + 1] += num[k]
            num = newnum
            den *= (xs[i] - xs[j])
        if den == 0:
            return None
        for k in range(len(num)):
            coef[k] += ys[i] * num[k] / den
    for c in coef:
        if c.denominator != 1:
            return False
    return True

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('bad input')
    plus = parameters.get('plus_inputs')
    minus = parameters.get('minus_inputs')
    t0 = parameters.get('external_point', 0)
    if not isinstance(plus, list) or not isinstance(minus, list):
        raise ValueError('bad input')
    if not isinstance(t0, int) or isinstance(t0, bool):
        raise ValueError('bad input')
    for v in plus + minus:
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError('bad input')
    if len(plus) == 0 or len(minus) == 0:
        raise ValueError('bad input')
    allpts = plus + minus
    if len(set(allpts)) != len(allpts):
        raise ValueError('overlap')
    if t0 in allpts:
        raise ValueError('external point in inputs')
    if len(allpts) > 12:
        raise ValueError('too many points')
    for v in allpts:
        if abs(v) > 10**6:
            raise ValueError('out of range')
    if abs(t0) > 10**6:
        raise ValueError('out of range')

    # Necessary condition: for i in plus, j in minus, 2a divisible by |i-j|
    M = 1
    for i in plus:
        for j in minus:
            d = abs(i - j)
            if d != 0:
                M = _lcm(M, d)
    # 2a ≡ 0 mod M  => a ≡ 0 mod M/gcd(M,2)
    g2 = math.gcd(M, 2)
    a_mod = M // g2

    # External point congruences: c = P(t0)
    # c ≡ a mod (t0 - i) for i in plus; c ≡ -a mod (t0 - j) for j in minus
    # Solve for (c, a) jointly. Represent a = a_mod * s, s>=1 integer.
    # Congruences: c - a ≡ 0 mod m_i ; c + a ≡ 0 mod m_j
    # Substitute a = a_mod * s.
    # We'll solve CRT over variables c and s.
    # Build congruences of form c + alpha*s ≡ 0 mod m, where alpha = -a_mod (plus) or +a_mod (minus)
    congs = []
    for i in plus:
        m = abs(t0 - i)
        if m != 0:
            congs.append(((-a_mod) % m, m))
    for j in minus:
        m = abs(t0 - j)
        if m != 0:
            congs.append((a_mod % m, m))

    # Solve c ≡ r_c mod L, and s ≡ r_s mod L_s via generalized CRT on (c, s)
    # We treat unknowns c and s. Use iterative CRT on combined modulus for c and s.
    # Represent solution set as c ≡ r_c mod L, s ≡ r_s mod L_s with same modulus L (coupled).
    # Start: c ≡ 0 mod 1, s ≡ 0 mod 1 (no constraint).
    # Each new congruence: c + alpha*s ≡ beta mod m.
    # We need to combine. This is a linear congruence in two vars; use CRT on c given s residue.
    # Simpler: iterate over possible s residues modulo L_s and check consistency; but L_s may grow.
    # Instead, solve via: for each congruence, substitute c = r_c + L*k, s = r_s + L_s*t.
    # Then r_c + L*k + alpha*(r_s + L_s*t) ≡ beta mod m.
    # => L*k + alpha*L_s*t ≡ beta - r_c - alpha*r_s mod m.
    # This is a linear congruence in k,t. We can solve by trying t modulo m/gcd(alpha*L_s, m) ...
    # To keep it simple and bounded, we'll do a search over s in a reasonable range and verify.

    # Since a_mod could be large, but for typical inputs small, we bound search.
    # Better: solve the system directly by enumerating s modulo L where L = lcm of all m's.
    # The congruences on (c,s) imply s satisfies: for each pair of congruences, consistency.
    # We'll compute the set of valid s modulo L via CRT on the derived congruences.
    # From c ≡ -alpha*s + beta mod m for each congruence, consistency between two:
    # -alpha1*s + beta1 ≡ -alpha2*s + beta2 mod gcd(m1,m2)
    # => (alpha2-alpha1)*s ≡ beta2-beta1 mod gcd(m1,m2)
    # This gives linear congruences on s. Solve them.

    s_congs = []
    n = len(congs)
    for x in range(n):
        b1, m1 = congs[x]
        for y in range(x + 1, n):
            b2, m2 = congs[y]
            g = math.gcd(m1, m2)
            # (alpha2 - alpha1)*s ≡ beta2 - beta1 mod g
            # Here alpha is implicit: congruence is c + alpha*s ≡ beta mod m
            # We stored beta = -alpha*a_mod? Wait, we stored (beta, m) where beta = -alpha*a_mod? No.
            # Let's recompute: congruence is c + alpha*s ≡ 0 mod m, with alpha = -a_mod (plus) or +a_mod (minus).
            # So beta = 0. We stored (0, m) but with alpha encoded? No, we stored ((-a_mod)%m, m) which is wrong.
            # Fix: store alpha and m.
            pass

    # Redo properly: store (alpha, m) for each congruence c + alpha*s ≡ 0 mod m
    alphas = []
    mods = []
    for i in plus:
        m = abs(t0 - i)
        if m != 0:
            alphas.append((-a_mod) % m)
            mods.append(m)
    for j in minus:
        m = abs(t0 - j)
        if m != 0:
            alphas.append(a_mod % m)
            mods.append(m)

    # Pairwise consistency: (alpha_y - alpha_x)*s ≡ 0 mod gcd(m_x, m_y)
    s_congs = []
    for x in range(len(mods)):
        for y in range(x + 1, len(mods)):
            g = math.gcd(mods[x], mods[y])
            if g == 1:
                continue
            coef = (alphas[y] - alphas[x]) % g
            # coef * s ≡ 0 mod g
            if coef == 0:
                continue
            gg = math.gcd(coef, g)
            # s ≡ 0 mod g/gg
            s_congs.append((0, g // gg))

    # Solve s congruences
    res = _solve_congruences(s_congs)
    if res is None:
        raise ValueError('no solution')
    s_r, s_m = res

    # Now find smallest positive s ≡ s_r mod s_m such that a = a_mod * s works.
    # Also need to verify sufficiency: there exists integer-coefficient polynomial.
    # We'll search s in arithmetic progression, check interpolation integrality for small cases.
    # For the given problem, we can check by constructing the polynomial via interpolation
    # and verifying integer coefficients. But that's expensive for large a.
    # Instead, use the fact that for integer-coefficient polynomial, the divided differences
    # must be integers. We'll check for candidate a by interpolation on the given points.

    # Bound search: try s up to some limit, but also use the necessary condition.
    # The minimal a is likely small. We'll search s from smallest positive in residue class.
    # To ensure correctness, we also need to check that the polynomial exists.
    # For the given problem, we can check by interpolation on the points plus t0.

    # We'll iterate s candidates in increasing order, compute a, and check if there's
    # an integer-coefficient polynomial through the points (plus, a), (minus, -a), (t0, c)
    # for some integer c satisfying the congruences.

    # To find c: from congruences c ≡ -alpha*s mod m, solve CRT for c.
    # Then check interpolation integrality.

    # Limit search to avoid infinite loop; but for valid inputs, minimal a should be found quickly.
    max_s = 10**6
    s = s_r if s_r > 0 else s_m
    if s == 0:
        s = s_m
    count = 0
    while s <= max_s and count < 10000:
        count += 1
        a = a_mod * s
        # Solve for c
        c_congs = []
        for idx in range(len(mods)):
            m = mods[idx]
            alpha = alphas[idx]
            # c ≡ -alpha*s mod m
            c_congs.append(((-alpha * s) % m, m))
        res_c = _solve_congruences(c_congs)
        if res_c is None:
            s += s_m
            continue
        c_r, c_m = res_c
        # Check interpolation integrality on points: plus->a, minus->-a, t0->c
        pts = [(x, a) for x in plus] + [(x, -a) for x in minus] + [(t0, c_r)]
        # Ensure distinct x
        if len(set(p[0] for p in pts)) != len(pts):
            s += s_m
            continue
        if _interp_integer(pts):
            return str(a)
        s += s_m

    raise ValueError('no solution found')
