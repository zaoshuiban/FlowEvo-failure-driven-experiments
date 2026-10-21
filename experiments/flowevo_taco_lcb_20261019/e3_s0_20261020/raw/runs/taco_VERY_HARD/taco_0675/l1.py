import sys
import math

INF = float('inf')
EPS = 1e-12


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    Ax, Ay, Az, vx, vy, vz, R = data[idx:idx + 7]
    idx += 7

    n = data[idx]
    idx += 1

    vv = vx * vx + vy * vy + vz * vz

    def valid_interval(c, e, low, high):
        # Returns interval of t such that low <= c + e*t <= high.
        if e == 0:
            if low - EPS <= c <= high + EPS:
                return -INF, INF
            return INF, -INF

        t1 = (low - c) / e
        t2 = (high - c) / e
        if t1 <= t2:
            return t1, t2
        return t2, t1

    def earliest_quad(Acoef, Bcoef, Ccoef, lo, hi):
        # Earliest t in [lo, hi] and t >= 0 such that
        # Acoef*t^2 + Bcoef*t + Ccoef <= 0.
        if hi < 0:
            if hi < -EPS:
                return INF
            hi = 0.0

        if lo < 0:
            lo = 0.0

        if hi < lo - EPS:
            return INF
        if hi < lo:
            hi = lo

        if Acoef == 0:
            if Bcoef == 0:
                if Ccoef <= 0:
                    return lo
                return INF

            root = -Ccoef / Bcoef

            if Bcoef > 0:
                if lo <= root + EPS:
                    return lo
                return INF
            else:
                t = max(lo, root)
                if t <= hi + EPS:
                    return max(0.0, t)
                return INF

        D = Bcoef * Bcoef - 4 * Acoef * Ccoef
        if D < 0:
            return INF

        sqrtD = math.sqrt(D)

        if Bcoef >= 0:
            q = -0.5 * (Bcoef + sqrtD)
        else:
            q = -0.5 * (Bcoef - sqrtD)

        if abs(q) < 1e-300:
            r1 = r2 = 0.0
        else:
            r1 = q / Acoef
            r2 = Ccoef / q
            if r1 > r2:
                r1, r2 = r2, r1

        t = max(lo, r1)
        if t < 0:
            t = 0.0

        upper = min(hi, r2)
        if t <= upper + 1e-10:
            return max(0.0, t)

        return INF

    def ball_time(ox, oy, oz, rad):
        wx = Ax - ox
        wy = Ay - oy
        wz = Az - oz

        Bcoef = 2 * (wx * vx + wy * vy + wz * vz)
        Ccoef = wx * wx + wy * wy + wz * wz - rad * rad

        return earliest_quad(vv, Bcoef, Ccoef, 0.0, INF)

    def segment_time(ox, oy, oz, px, py, pz, rad):
        L2 = px * px + py * py + pz * pz

        if L2 == 0:
            return ball_time(ox, oy, oz, rad)

        wx = Ax - ox
        wy = Ay - oy
        wz = Az - oz

        cp = wx * px + wy * py + wz * pz
        ep = vx * px + vy * py + vz * pz

        best = INF

        # Start cap: closest point is O.
        lo, hi = valid_interval(cp, ep, -INF, 0.0)
        if lo <= hi + EPS:
            Bcoef = 2 * (wx * vx + wy * vy + wz * vz)
            Ccoef = wx * wx + wy * wy + wz * wz - rad * rad
            t = earliest_quad(vv, Bcoef, Ccoef, lo, hi)
            if t < best:
                best = t

        # Cylinder part: projection lies inside the segment.
        lo, hi = valid_interval(cp, ep, 0.0, float(L2))
        if lo <= hi + EPS:
            wv = wx * vx + wy * vy + wz * vz

            Acoef = L2 * vv - ep * ep
            Bcoef = 2 * L2 * wv - 2 * cp * ep
            Ccoef = L2 * (wx * wx + wy * wy + wz * wz) - cp * cp - rad * rad * L2

            t = earliest_quad(Acoef, Bcoef, Ccoef, lo, hi)
            if t < best:
                best = t

        # End cap: closest point is O + p.
        qx = ox + px
        qy = oy + py
        qz = oz + pz

        wx2 = Ax - qx
        wy2 = Ay - qy
        wz2 = Az - qz

        lo, hi = valid_interval(cp, ep, float(L2), INF)
        if lo <= hi + EPS:
            Bcoef = 2 * (wx2 * vx + wy2 * vy + wz2 * vz)
            Ccoef = wx2 * wx2 + wy2 * wy2 + wz2 * wz2 - rad * rad
            t = earliest_quad(vv, Bcoef, Ccoef, lo, hi)
            if t < best:
                best = t

        return best

    answer = INF

    for _ in range(n):
        ox, oy, oz, ri, mi = data[idx:idx + 5]
        idx += 5

        # Mine body.
        t = ball_time(ox, oy, oz, R + ri)
        if t < answer:
            answer = t

        # Mine spikes.
        for _ in range(mi):
            px, py, pz = data[idx:idx + 3]
            idx += 3

            t = segment_time(ox, oy, oz, px, py, pz, R)
            if t < answer:
                answer = t

    if math.isinf(answer):
        print("-1")
    else:
        print(f"{answer:.12f}")


if __name__ == "__main__":
    solve()