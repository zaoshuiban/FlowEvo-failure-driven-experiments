import sys
from decimal import Decimal, getcontext

getcontext().prec = 60

INF = Decimal('1e100')
ZERO = Decimal(0)


def earliest_ball(A, v, C, radius):
    """Earliest t >= 0 such that |A + v*t - C| <= radius."""
    dx = A[0] - C[0]
    dy = A[1] - C[1]
    dz = A[2] - C[2]

    a = v[0] * v[0] + v[1] * v[1] + v[2] * v[2]
    b = 2 * (dx * v[0] + dy * v[1] + dz * v[2])
    c = dx * dx + dy * dy + dz * dz - radius * radius

    if c <= 0:
        return ZERO

    # If b >= 0, distance is non-decreasing for t >= 0, so no future hit.
    if b >= 0:
        return INF

    D = b * b - 4 * a * c
    if D < 0:
        return INF

    sqrtD = Decimal(D).sqrt()
    den = Decimal(2 * a)

    # Both roots are positive in this case.
    r2 = (-Decimal(b) + sqrtD) / den
    if r2 <= 0:
        return INF

    # Product of roots is c / a, so the smaller positive root is:
    r1 = Decimal(c) / (Decimal(a) * r2)
    return r1


def quad_interval(a, b, c):
    """
    Returns interval (lo, hi) where a*t^2 + b*t + c <= 0.
    Here a >= 0 and a, b, c are integers.
    Returns None if no real solution.
    """
    if a == 0:
        if b == 0:
            if c <= 0:
                return (-INF, INF)
            return None

        root = -Decimal(c) / Decimal(b)
        if b > 0:
            return (-INF, root)
        else:
            return (root, INF)

    D = b * b - 4 * a * c
    if D < 0:
        return None

    sqrtD = Decimal(D).sqrt()
    den = Decimal(2 * a)

    r1 = (-Decimal(b) - sqrtD) / den
    r2 = (-Decimal(b) + sqrtD) / den

    if r1 > r2:
        r1, r2 = r2, r1

    return (r1, r2)


def earliest_spike_interior(A, v, O, p, R):
    """
    Earliest t >= 0 such that the closest point on the infinite line
    O + s*p has 0 <= s <= 1 and is within distance R from A + v*t.
    """
    L = p[0] * p[0] + p[1] * p[1] + p[2] * p[2]
    if L == 0:
        return INF

    d = (A[0] - O[0], A[1] - O[1], A[2] - O[2])

    vp = v[0] * p[0] + v[1] * p[1] + v[2] * p[2]
    dp = d[0] * p[0] + d[1] * p[1] + d[2] * p[2]

    # Projection parameter s(t) = (dp + vp*t) / L.
    # Need 0 <= s(t) <= 1.
    if vp == 0:
        if dp < 0 or dp > L:
            return INF
        proj_lo = -INF
        proj_hi = INF
    else:
        t0 = Decimal(-dp) / Decimal(vp)       # s = 0
        t1 = Decimal(L - dp) / Decimal(vp)    # s = 1
        if t0 < t1:
            proj_lo, proj_hi = t0, t1
        else:
            proj_lo, proj_hi = t1, t0

    # Distance to the line using cross product:
    # |(d + v*t) x p|^2 <= R^2 * |p|^2
    c0x = d[1] * p[2] - d[2] * p[1]
    c0y = d[2] * p[0] - d[0] * p[2]
    c0z = d[0] * p[1] - d[1] * p[0]

    cvx = v[1] * p[2] - v[2] * p[1]
    cvy = v[2] * p[0] - v[0] * p[2]
    cvz = v[0] * p[1] - v[1] * p[0]

    a = cvx * cvx + cvy * cvy + cvz * cvz
    b = 2 * (c0x * cvx + c0y * cvy + c0z * cvz)
    c = c0x * c0x + c0y * c0y + c0z * c0z - R * R * L

    interval = quad_interval(a, b, c)
    if interval is None:
        return INF

    q_lo, q_hi = interval

    lo = ZERO
    if q_lo > lo:
        lo = q_lo
    if proj_lo > lo:
        lo = proj_lo

    hi = q_hi
    if proj_hi < hi:
        hi = proj_hi

    if lo <= hi:
        return lo

    return INF


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0

    Ax, Ay, Az, vx, vy, vz, R = data[idx:idx + 7]
    idx += 7

    n = data[idx]
    idx += 1

    A = (Ax, Ay, Az)
    v = (vx, vy, vz)

    answer = INF

    for _ in range(n):
        Ox, Oy, Oz, ri, mi = data[idx:idx + 5]
        idx += 5

        O = (Ox, Oy, Oz)

        # Mine body
        t = earliest_ball(A, v, O, R + ri)
        if t < answer:
            answer = t

        for _ in range(mi):
            px, py, pz = data[idx:idx + 3]
            idx += 3

            p = (px, py, pz)
            P = (Ox + px, Oy + py, Oz + pz)

            # Endpoint P of the spike
            t = earliest_ball(A, v, P, R)
            if t < answer:
                answer = t

            # Interior of the spike
            t = earliest_spike_interior(A, v, O, p, R)
            if t < answer:
                answer = t

    if answer >= INF / 2:
        print("-1")
    else:
        print(f"{answer:.10f}")


if __name__ == "__main__":
    main()