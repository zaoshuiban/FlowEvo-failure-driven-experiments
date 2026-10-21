import sys
import math

INF = float('inf')
EPS = 1e-12


def linear_le(c0, c1):
    # Returns interval of t where c0 + c1 * t <= 0.
    if c1 == 0:
        if c0 <= 0:
            return (-INF, INF)
        return None

    root = -c0 / c1
    if c1 > 0:
        return (-INF, root)
    else:
        return (root, INF)


def linear_ge(c0, c1):
    # Returns interval of t where c0 + c1 * t >= 0.
    return linear_le(-c0, -c1)


def quad_leq(a, b, c):
    # Returns interval of t where a*t^2 + b*t + c <= 0.
    # Here a is always >= 0.
    if a == 0:
        if b == 0:
            if c <= 0:
                return (-INF, INF)
            return None

        root = -c / b
        if b > 0:
            return (-INF, root)
        else:
            return (root, INF)

    d = b * b - 4 * a * c
    if d < 0:
        return None

    if d == 0:
        root = -b / (2.0 * a)
        return (root, root)

    sqrt_d = math.sqrt(d)
    den = 2.0 * a
    lo = (-b - sqrt_d) / den
    hi = (-b + sqrt_d) / den
    return (lo, hi)


def intersect(i1, i2):
    if i1 is None or i2 is None:
        return None

    lo = max(i1[0], i2[0])
    hi = min(i1[1], i2[1])

    if lo <= hi + 1e-10:
        return (lo, hi)
    return None


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    ax, ay, az, vx, vy, vz, R = data[idx:idx + 7]
    idx += 7

    n = data[idx]
    idx += 1

    speed2 = vx * vx + vy * vy + vz * vz
    R2 = R * R

    best = INF

    def consider(interval):
        nonlocal best
        if interval is None:
            return

        lo, hi = interval
        if hi < 0:
            return

        t = lo
        if t < 0:
            t = 0.0

        if t <= hi + 1e-10 and t < best:
            best = t

    for _ in range(n):
        ox, oy, oz, r, m = data[idx:idx + 5]
        idx += 5

        wx = ax - ox
        wy = ay - oy
        wz = az - oz

        w0v = wx * vx + wy * vy + wz * vz
        w0sq = wx * wx + wy * wy + wz * wz

        # Collision with the spherical body of the mine.
        rad = R + r
        consider(quad_leq(speed2, 2 * w0v, w0sq - rad * rad))

        for _ in range(m):
            px, py, pz = data[idx:idx + 3]
            idx += 3

            length2 = px * px + py * py + pz * pz
            if length2 == 0:
                # The spike is just the center point, already covered by the body.
                continue

            d0 = wx * px + wy * py + wz * pz
            d1 = vx * px + vy * py + vz * pz

            # Projection parameter s(t) <= 0: closest point is O.
            sphere_o = quad_leq(speed2, 2 * w0v, w0sq - R2)
            reg_le0 = linear_le(d0, d1)
            consider(intersect(sphere_o, reg_le0))

            # 0 <= s(t) <= 1: distance to the infinite line through O and O+p.
            a2 = length2 * speed2 - d1 * d1
            a1 = 2 * (length2 * w0v - d0 * d1)
            a0 = length2 * (w0sq - R2) - d0 * d0

            cylinder = quad_leq(a2, a1, a0)

            reg_ge0 = linear_ge(d0, d1)
            reg_le1 = linear_le(d0 - length2, d1)
            reg_mid = intersect(reg_ge0, reg_le1)

            consider(intersect(cylinder, reg_mid))

            # Projection parameter s(t) >= 1: closest point is O+p.
            bx = wx - px
            by = wy - py
            bz = wz - pz

            b_dot_v = bx * vx + by * vy + bz * vz
            b_sq = bx * bx + by * by + bz * bz

            sphere_b = quad_leq(speed2, 2 * b_dot_v, b_sq - R2)
            reg_ge1 = linear_ge(d0 - length2, d1)

            consider(intersect(sphere_b, reg_ge1))

    if best == INF:
        sys.stdout.write("-1\n")
    else:
        sys.stdout.write(f"{best:.12f}\n")


if __name__ == "__main__":
    solve()