import math
import itertools

def _icbrt(n):
    if n < 0:
        return -_icbrt(-n)
    r = int(round(n ** (1.0/3.0)))
    while (r+1)**3 <= n:
        r += 1
    while r**3 > n:
        r -= 1
    return r

def _is_cube(n):
    if n < 0:
        return False
    r = _icbrt(n)
    return r*r*r == n

def _cube_free_part(n):
    # returns (s, m) with n = s^3 * m, m cube-free
    if n == 0:
        return (0, 1)
    sign = 1
    if n < 0:
        sign = -1
        n = -n
    s = 1
    m = 1
    d = 2
    while d*d*d <= n:
        e = 0
        while n % d == 0:
            n //= d
            e += 1
        s *= d ** (e // 3)
        if e % 3 == 1:
            m *= d
        elif e % 3 == 2:
            m *= d*d
        d += 1
    # remaining n is 1, prime, or product of two primes; check cube
    if n > 1:
        r = _icbrt(n)
        if r*r*r == n:
            s *= r
        else:
            m *= n
    return (sign*s, m)

def _min_poly_sum_diff(a, b, c):
    # Compute minimal polynomial of x+y-z where x^3=a, y^3=b, z^3=c.
    # Use resultant approach: eliminate x,y,z.
    # We'll compute polynomial of t = x+y-z by resultants step by step.
    # Represent polynomials as dicts {exponent: coeff} in variable t.
    # Start with x: x^3 - a = 0. We want to eliminate x from (t - y + z - x) = 0? 
    # Better: t = x+y-z => x = t - y + z. Substitute into x^3=a:
    # (t - y + z)^3 - a = 0. This is polynomial in t,y,z.
    # Then eliminate y using y^3=b, z using z^3=c.
    # We'll do resultants numerically via companion matrices? Too heavy.
    # Instead: use the fact that the field Q(cbrt(a),cbrt(b),cbrt(c)) has degree dividing 27.
    # We can compute the minimal polynomial by finding the product over conjugates.
    # Conjugates: x -> omega^i * cbrt(a), y -> omega^j * cbrt(b), z -> omega^k * cbrt(c)
    # where omega = exp(2*pi*i/3). t = x+y-z.
    # The minimal polynomial divides the product over all 27 combinations of (T - t).
    # We can compute this product symbolically using complex arithmetic with high precision,
    # then round coefficients to integers. This is exact if precision is sufficient.
    # Use Python complex numbers with high precision via fractions? Use mpmath? Not allowed.
    # Use exact arithmetic with sympy? Not allowed.
    # Alternative: compute the polynomial with integer coefficients by working in the ring Z[omega].
    # omega satisfies omega^2+omega+1=0. Represent numbers as pairs (u,v) meaning u+v*omega.
    # cbrt(a) is real. omega^i * cbrt(a) = cbrt(a) * omega^i.
    # So t = cbrt(a)*omega^i + cbrt(b)*omega^j - cbrt(c)*omega^k.
    # We need product over i,j,k in {0,1,2} of (T - t).
    # This product is symmetric in the conjugates, so coefficients are rational integers.
    # We can compute this product using exact arithmetic in Z[omega] by representing
    # each t as a polynomial in omega with coefficients involving cbrt(a),cbrt(b),cbrt(c).
    # But cbrt(a) etc. are not in Z[omega]; they are real algebraic numbers.
    # However, the product over all conjugates will be a polynomial in T with integer coefficients.
    # We can compute it by evaluating numerically with high precision and rounding.
    # Use Python's decimal module for high precision.
    from decimal import Decimal, getcontext
    getcontext().prec = 80
    # Compute cbrt(a), cbrt(b), cbrt(c) as Decimals
    def dcbrt(n):
        if n == 0:
            return Decimal(0)
        # Newton's method
        x = Decimal(n) ** (Decimal(1)/Decimal(3))
        for _ in range(100):
            x = (2*x + Decimal(n)/(x*x)) / 3
        return x
    ca = dcbrt(a)
    cb = dcbrt(b)
    cc = dcbrt(c)
    # omega = exp(2*pi*i/3) = -1/2 + i*sqrt(3)/2
    # We'll use complex numbers with Decimal real and imaginary parts.
    # Represent as (re, im) tuples of Decimals.
    sqrt3 = Decimal(3).sqrt()
    omega_re = Decimal(-1)/2
    omega_im = sqrt3/2
    # powers of omega
    def omega_pow(k):
        k = k % 3
        if k == 0:
            return (Decimal(1), Decimal(0))
        if k == 1:
            return (omega_re, omega_im)
        # k==2: omega^2 = -1/2 - i*sqrt(3)/2
        return (omega_re, -omega_im)
    # complex multiply
    def cmul(x, y):
        return (x[0]*y[0] - x[1]*y[1], x[0]*y[1] + x[1]*y[0])
    def cadd(x, y):
        return (x[0]+y[0], x[1]+y[1])
    def csub(x, y):
        return (x[0]-y[0], x[1]-y[1])
    # Build list of 27 t values
    ts = []
    for i in range(3):
        oi = omega_pow(i)
        xi = cmul((ca, Decimal(0)), oi)
        for j in range(3):
            oj = omega_pow(j)
            yj = cmul((cb, Decimal(0)), oj)
            for k in range(3):
                ok = omega_pow(k)
                zk = cmul((cc, Decimal(0)), ok)
                t = csub(cadd(xi, yj), zk)
                ts.append(t)
    # Compute polynomial P(T) = product (T - t) as complex polynomial with Decimal coefficients.
    # Represent polynomial as list of complex coefficients [c0, c1, ..., c27] for T^0..T^27.
    poly = [(Decimal(1), Decimal(0))]  # constant 1
    for t in ts:
        # multiply poly by (T - t)
        newpoly = [(Decimal(0), Decimal(0))] * (len(poly)+1)
        for idx, coef in enumerate(poly):
            # coef * T^(idx+1)
            newpoly[idx+1] = cadd(newpoly[idx+1], coef)
            # coef * (-t) * T^idx
            negt = (Decimal(0)-t[0], Decimal(0)-t[1])
            newpoly[idx] = cadd(newpoly[idx], cmul(coef, negt))
        poly = newpoly
    # The coefficients should be real integers (imaginary part ~0).
    # Round to nearest integer.
    coeffs = []
    for coef in poly:
        re = coef[0]
        im = coef[1]
        # check imaginary part is small
        if abs(im) > Decimal('1e-20'):
            # not real? should not happen
            pass
        # round re to nearest integer
        ri = int(re.to_integral_value())
        coeffs.append(ri)
    # Remove leading zeros (should be monic, leading coeff 1)
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    return coeffs

def _min_poly_target(k, p, q):
    # T = k * sqrt(cbrt(p) - cbrt(q))
    # T^2 = k^2 * (cbrt(p) - cbrt(q))
    # Let u = cbrt(p) - cbrt(q). Then u satisfies a cubic.
    # u^3 = p - q - 3*cbrt(pq)*u
    # So (u^3 - (p-q))^3 = -27*pq*u^3? Let's derive.
    # u = cbrt(p) - cbrt(q)
    # u^3 = p - q - 3*cbrt(pq)*(cbrt(p)-cbrt(q)) = p - q - 3*cbrt(pq)*u
    # So u^3 + 3*cbrt(pq)*u - (p-q) = 0
    # Let v = cbrt(pq). Then u^3 + 3*v*u - (p-q) = 0, and v^3 = pq.
    # Eliminate v: v = ((p-q) - u^3)/(3u) if u != 0.
    # v^3 = pq => ((p-q)-u^3)^3 / (27*u^3) = pq
    # => ((p-q)-u^3)^3 = 27*pq*u^3
    # Let w = u^3. Then (p-q-w)^3 = 27*pq*w.
    # Expand: (p-q)^3 - 3(p-q)^2 w + 3(p-q) w^2 - w^3 = 27*pq*w
    # => -w^3 + 3(p-q)w^2 - 3(p-q)^2 w + (p-q)^3 - 27pq w = 0
    # => w^3 - 3(p-q)w^2 + (3(p-q)^2 + 27pq) w - (p-q)^3 = 0
    # So w = u^3 satisfies cubic: w^3 - 3(p-q)w^2 + (3(p-q)^2+27pq)w - (p-q)^3 = 0.
    # Now T^2 = k^2 * u, so u = T^2/k^2. Then w = u^3 = T^6/k^6.
    # Substitute w = T^6/k^6 into cubic and multiply by k^18:
    # (T^6/k^6)^3 - 3(p-q)(T^6/k^6)^2 + (3(p-q)^2+27pq)(T^6/k^6) - (p-q)^3 = 0
    # Multiply by k^18:
    # T^18 - 3(p-q)k^6 T^12 + (3(p-q)^2+27pq)k^12 T^6 - (p-q)^3 k^18 = 0
    # This is a polynomial in T^6. Let y = T^6. Then y^3 - 3(p-q)k^6 y^2 + (3(p-q)^2+27pq)k^12 y - (p-q)^3 k^18 = 0.
    # But T itself satisfies a degree 6 polynomial? Actually T^2 = k^2 u, u has degree 3 over Q (unless special).
    # So T has degree 6 over Q. The minimal polynomial of T is obtained by eliminating u from T^2 = k^2 u and the cubic for u.
    # Let's compute the minimal polynomial of T directly using resultants.
    # We have u = T^2/k^2. The cubic for u: u^3 - 3(p-q)u^2 + (3(p-q)^2+27pq)u - (p-q)^3 = 0.
    # Substitute u = T^2/k^2:
    # (T^6/k^6) - 3(p-q)(T^4/k^4) + (3(p-q)^2+27pq)(T^2/k^2) - (p-q)^3 = 0
    # Multiply by k^6:
    # T^6 - 3(p-q)k^2 T^4 + (3(p-q)^2+27pq)k^4 T^2 - (p-q)^3 k^6 = 0
    # This is a polynomial in T of degree 6. Let's verify: T^2 = k^2 u, so T^6 = k^6 u^3, etc.
    # Yes, this is the minimal polynomial of T (assuming u is not rational, which it isn't for p!=q).
    # So minimal polynomial of T: T^6 - 3(p-q)k^2 T^4 + (3(p-q)^2+27pq)k^4 T^2 - (p-q)^3 k^6 = 0.
    # Let's return coefficients [c0, c1, ..., c6] for T^0..T^6.
    c0 = -(p-q)**3 * k**6
    c2 = (3*(p-q)**2 + 27*p*q) * k**4
    c4 = -3*(p-q)*k**2
    c6 = 1
    return [c0, 0, c2, 0, c4, 0, c6]

def _poly_equal(p1, p2):
    # compare two polynomials given as coefficient lists (low to high)
    # trim trailing zeros
    def trim(p):
        p = list(p)
        while len(p) > 1 and p[-1] == 0:
            p.pop()
        return p
    p1 = trim(p1)
    p2 = trim(p2)
    if len(p1) != len(p2):
        return False
    for a, b in zip(p1, p2):
        if a != b:
            return False
    return True

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['p', 'q', 'k', 'N']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
    p = parameters['p']
    q = parameters['q']
    k = parameters['k']
    N = parameters['N']
    return_sum = parameters.get('return_sum', True)
    # validate types: booleans are not integers
    for name, val in [('p', p), ('q', q), ('k', k), ('N', N)]:
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(name + ' must be an integer')
    if p <= 0 or q <= 0 or k <= 0 or N <= 0:
        raise ValueError('p, q, k, N must be positive integers')
    if p == q:
        raise ValueError('p and q must be distinct')
    if N > 200:
        raise ValueError('N too large')
    # compute target minimal polynomial
    target_poly = _min_poly_target(k, p, q)
    # search for triple (a,b,c) with 1<=a,b,c<=N
    # We need S = cbrt(a)+cbrt(b)-cbrt(c) to have the same minimal polynomial as T.
    # Note: S may have degree less than 27 if a,b,c are not cube-free or have relations.
    # We'll compute the minimal polynomial of S using the product over conjugates method.
    # To speed up, we can first check numerical approximation.
    # Compute target value numerically: T = k * sqrt(cbrt(p) - cbrt(q))
    # Use float for quick filtering.
    def fcbrt(n):
        return n ** (1.0/3.0)
    try:
        inner = fcbrt(p) - fcbrt(q)
        if inner <= 0:
            # cbrt(p) - cbrt(q) could be negative if p<q, but then sqrt is imaginary.
            # The problem likely has p>q. If inner < 0, no real solution.
            raise ValueError('cbrt(p)-cbrt(q) must be nonnegative')
        T_float = k * math.sqrt(inner)
    except Exception:
        raise ValueError('invalid p,q for real square root')
    # We'll search all triples. To reduce work, note that S = cbrt(a)+cbrt(b)-cbrt(c).
    # We can compute S_float and compare to T_float within tolerance.
    # But we need exact match. We'll use the minimal polynomial check.
    # However, computing minimal polynomial for each triple is expensive (27 conjugates with high precision).
    # We can first filter by numerical value: |S_float - T_float| < 1e-6.
    # Then do exact check.
    candidates = []
    for a in range(1, N+1):
        ca = fcbrt(a)
        for b in range(1, N+1):
            cb = fcbrt(b)
            for c in range(1, N+1):
                cc = fcbrt(c)
                S_float = ca + cb - cc
                if abs(S_float - T_float) < 1e-6:
                    candidates.append((a,b,c))
    # Now for each candidate, compute minimal polynomial and compare.
    # But we need to be careful: the minimal polynomial of S might be a factor of the product over 27 conjugates.
    # The product over 27 conjugates gives a polynomial of degree up to 27, but the minimal polynomial is the minimal degree factor.
    # Our _min_poly_sum_diff computes the full product over 27 conjugates, which is a multiple of the minimal polynomial.
    # The target polynomial has degree 6. So we need to check if the target polynomial divides the product polynomial.
    # Actually, if S has the same minimal polynomial as T, then the minimal polynomial of S is the target polynomial.
    # The product polynomial for S will be a power of the minimal polynomial (since all conjugates are roots).
    # So we can check if the target polynomial divides the product polynomial.
    # But computing the product polynomial for each candidate is expensive.
    # Instead, we can compute the minimal polynomial of S by finding the minimal degree factor of the product polynomial that has S as a root.
    # That's complex. Alternative: use the fact that if S = T, then S satisfies the target polynomial.
    # So we can just check if S satisfies the target polynomial exactly.
    # How to check if S satisfies a polynomial with integer coefficients?
    # We can compute the value of the polynomial at S using exact arithmetic in the field Q(cbrt(a),cbrt(b),cbrt(c)).
    # That's also complex.
    # Simpler: use numerical evaluation with high precision and check if the polynomial evaluates to near zero.
    # Since the polynomial has integer coefficients and S is algebraic of degree at most 27, if the polynomial is not zero at S, the value is at least some bound away from zero.
    # We can use high precision (e.g., 100 digits) to distinguish.
    # Let's do that: for each candidate, evaluate target_poly at S using high precision complex arithmetic.
    # If the absolute value is < 1e-50, accept.
    from decimal import Decimal, getcontext
    getcontext().prec = 100
    def dcbrt_high(n):
        if n == 0:
            return Decimal(0)
        x = Decimal(n) ** (Decimal(1)/Decimal(3))
        for _ in range(200):
            x = (2*x + Decimal(n)/(x*x)) / 3
        return x
    # Precompute cube roots for 1..N
    cbrt_cache = {}
    for i in range(1, N+1):
        cbrt_cache[i] = dcbrt_high(i)
    # target polynomial coefficients (low to high)
    # target_poly is list of ints
    found = None
    for (a,b,c) in candidates:
        ca = cbrt_cache[a]
        cb = cbrt_cache[b]
        cc = cbrt_cache[c]
        S = ca + cb - cc
        # evaluate polynomial at S
        val = Decimal(0)
        # Horner's method
        for coef in reversed(target_poly):
            val = val * S + Decimal(coef)
        if abs(val) < Decimal('1e-50'):
            found = (a,b,c)
            break
    if found is None:
        # try all triples without numerical filter? too slow. But maybe the filter missed due to precision.
        # We'll do a broader search with looser filter.
        for a in range(1, N+1):
            ca = cbrt_cache[a]
            for b in range(1, N+1):
                cb = cbrt_cache[b]
                for c in range(1, N+1):
                    cc = cbrt_cache[c]
                    S = ca + cb - cc
                    val = Decimal(0)
                    for coef in reversed(target_poly):
                        val = val * S + Decimal(coef)
                    if abs(val) < Decimal('1e-50'):
                        found = (a,b,c)
                        break
                if found:
                    break
            if found:
                break
    if found is None:
        raise ValueError('no solution found within bound N')
    a,b,c = found
    if return_sum:
        return str(a+b+c)
    else:
        return str((a,b,c))
