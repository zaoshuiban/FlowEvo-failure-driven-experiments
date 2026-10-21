import sys
import math

INF = float("inf")


def sphere_entry(dx, dy, dz, vx, vy, vz, radius):
    # Earliest t >= 0 such that |(dx,dy,dz) + t*(vx,vy,vz)| <= radius
    a = vx * vx + vy * vy + vz * vz
    b = 2 * (dx * vx + dy * vy + dz * vz)
    c = dx * dx + dy * dy + dz * dz - radius * radius

    if c <= 0:
        return 0.0

    disc = b * b - 4 * a * c
    if disc < 0:
        return None

    sqrt_disc = math.sqrt(disc)
    t = (-b - sqrt_disc) / (2 * a)

    if t >= -1e-12:
        return max(0.0, t)

    return None


def cylinder_entry(dx, dy, dz, vx, vy, vz, px, py, pz, radius):
    # Earliest t >= 0 such that:
    # distance from (dx,dy,dz)+t*(vx,vy,vz) to the infinite line through p is <= radius
    # and projection parameter is in [0, 1].
    length2 = px * px + py * py + pz * pz
    if length2 == 0:
        return None

    vv = vx * vx + vy * vy + vz * vz
    dd = dx * dx + dy * dy + dz * dz

    dv = dx * vx + dy * vy + dz * vz
    dp = dx * px + dy * py + dz * pz
    vp = vx * px + vy * py + vz * pz

    # Inequality after multiplying by length2:
    # A*t^2 + B*t + C <= 0
    A = vv * length2 - vp * vp
    B = 2 * (dv * length2 - dp * vp)
    C = dd * length2 - dp * dp - radius * radius * length2

    if A == 0:
        if C <= 0:
            radial_lo = -INF
            radial_hi = INF
        else:
            return None
    else:
        disc = B * B - 4 * A * C
        if disc < 0:
            return None

        sqrt_disc = math.sqrt(disc)
        den = 2 * A
        radial_lo = (-B - sqrt_disc) / den
        radial_hi = (-B + sqrt_disc) / den

    # Projection parameter s satisfies 0 <= dp + vp*t <= length2
    q0 = dp
    qv = vp

    if qv == 0:
        if q0 < 0 or q0 > length2:
            return None
        axis_lo = -INF
        axis_hi = INF
    else:
        t0 = -q0 / qv
        t1 = (length2 - q0) / qv
        if t0 < t1:
            axis_lo, axis_hi = t0, t1
        else:
            axis_lo, axis_hi = t1, t0

    lo = max(radial_lo, axis_lo, 0.0)
    hi = min(radial_hi, axis_hi)

    if lo <= hi + 1e-10:
        return max(0.0, lo)

    return None


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0

    Ax = data[idx]
    Ay = data[idx + 1]
    Az = data[idx + 2]
    vx = data[idx + 3]
    vy = data[idx + 4]
    vz = data[idx + 5]
    R = data[idx + 6]
    idx += 7

    n = data[idx]
    idx += 1

    answer = INF

    for _ in range(n):
        Ox = data[idx]
        Oy = data[idx + 1]
        Oz = data[idx + 2]
        ri = data[idx + 3]
        mi = data[idx + 4]
        idx += 5

        dx = Ax - Ox
        dy = Ay - Oy
        dz = Az - Oz

        # Mine body: sphere of radius ri, Death Star radius R.
        t = sphere_entry(dx, dy, dz, vx, vy, vz, R + ri)
        if t is not None and t < answer:
            answer = t

        for _ in range(mi):
            px = data[idx]
            py = data[idx + 1]
            pz = data[idx + 2]
            idx += 3

            # Endpoint P = O + p.
            t = sphere_entry(dx - px, dy - py, dz - pz, vx, vy, vz, R)
            if t is not None and t < answer:
                answer = t

            # Cylindrical part of the capsule around the spike segment.
            t = cylinder_entry(dx, dy, dz, vx, vy, vz, px, py, pz, R)
            if t is not None and t < answer:
                answer = t

    if math.isinf(answer):
        print("-1")
    else:
        print(f"{answer:.10f}")


if __name__ == "__main__":
    main()