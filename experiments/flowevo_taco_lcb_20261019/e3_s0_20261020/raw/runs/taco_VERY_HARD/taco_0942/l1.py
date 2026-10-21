import sys
import itertools

PX = [0, 1, 0, 1]
PY = [0, 0, 1, 1]

INF = 10 ** 30
HIGH = 10 ** 18


def ceil_div(a, b):
    return -((-a) // b)


def add_linear(lo, hi, alpha, beta, low, high):
    # low <= alpha * s + beta <= high
    if alpha == 0:
        return lo, hi, low <= beta <= high

    if alpha > 0:
        lb = ceil_div(low - beta, alpha)
        ub = (high - beta) // alpha
    else:
        ub = (low - beta) // alpha
        lb = ceil_div(high - beta, alpha)

    if lb > lo:
        lo = lb
    if ub < hi:
        hi = ub
    return lo, hi, lo <= hi


def add_leq(lo, hi, alpha, beta):
    # alpha * s <= beta
    if alpha == 0:
        return lo, hi, beta >= 0

    if alpha > 0:
        ub = beta // alpha
        if ub < hi:
            hi = ub
    else:
        lb = ceil_div(beta, alpha)
        if lb > lo:
            lo = lb

    return lo, hi, lo <= hi


def solve_case(L, perm, mask, pts, construct):
    if L < 0:
        return None

    V = []
    H = []

    for r in range(4):
        i = perm[r]
        p = PX[r]
        q = PY[r]
        x, y = pts[i]
        rec = (r, p, q, x, y, i)

        if (mask >> r) & 1:
            H.append(rec)
        else:
            V.append(rec)

    # Determine a from vertical-moving bots:
    # a + p * s = x
    c0a = None
    c1a = None

    for _, p, _, x, _, _ in V:
        if p == 0:
            if c0a is None:
                c0a = x
            elif c0a != x:
                return None
        else:
            if c1a is None:
                c1a = x
            elif c1a != x:
                return None

    sfixA = None

    if c0a is None and c1a is None:
        a_free = True
        a0 = 0
        a_coef = 0
    else:
        a_free = False
        if c0a is not None and c1a is not None:
            sfixA = c1a - c0a
            a0 = c0a
            a_coef = 0
        elif c0a is not None:
            a0 = c0a
            a_coef = 0
        else:
            a0 = c1a
            a_coef = -1

    # Determine b from horizontal-moving bots:
    # b + q * s = y
    c0b = None
    c1b = None

    for _, _, q, _, y, _ in H:
        if q == 0:
            if c0b is None:
                c0b = y
            elif c0b != y:
                return None
        else:
            if c1b is None:
                c1b = y
            elif c1b != y:
                return None

    sfixB = None

    if c0b is None and c1b is None:
        b_free = True
        b0 = 0
        b_coef = 0
    else:
        b_free = False
        if c0b is not None and c1b is not None:
            sfixB = c1b - c0b
            b0 = c0b
            b_coef = 0
        elif c0b is not None:
            b0 = c0b
            b_coef = 0
        else:
            b0 = c1b
            b_coef = -1

    lo = 1
    hi = INF

    if sfixA is not None:
        lo = max(lo, sfixA)
        hi = min(hi, sfixA)

    if sfixB is not None:
        lo = max(lo, sfixB)
        hi = min(hi, sfixB)

    if lo > hi:
        return None

    # For horizontal-moving bots, their y is fixed, so:
    # |a + p*s - x| <= L
    if H:
        if a_free:
            for _, pj, _, xj, _, _ in H:
                for _, pk, _, xk, _, _ in H:
                    alpha = pk - pj
                    beta = 2 * L + xk - xj
                    lo, hi, ok = add_leq(lo, hi, alpha, beta)
                    if not ok:
                        return None
        else:
            for _, p, _, x, _, _ in H:
                alpha = a_coef + p
                beta = a0
                lo, hi, ok = add_linear(lo, hi, alpha, beta, x - L, x + L)
                if not ok:
                    return None

    # For vertical-moving bots, their x is fixed, so:
    # |b + q*s - y| <= L
    if V:
        if b_free:
            for _, _, qi, _, yi, _ in V:
                for _, _, qk, _, yk, _ in V:
                    alpha = qk - qi
                    beta = 2 * L + yk - yi
                    lo, hi, ok = add_leq(lo, hi, alpha, beta)
                    if not ok:
                        return None
        else:
            for _, _, q, _, y, _ in V:
                alpha = b_coef + q
                beta = b0
                lo, hi, ok = add_linear(lo, hi, alpha, beta, y - L, y + L)
                if not ok:
                    return None

    if lo > hi:
        return None

    s = lo

    if a_free:
        if H:
            a = -INF
            for _, p, _, x, _, _ in H:
                a = max(a, x - p * s - L)
        else:
            a = 0
    else:
        a = a0 + a_coef * s

    if b_free:
        if V:
            b = -INF
            for _, _, q, _, y, _ in V:
                b = max(b, y - q * s - L)
        else:
            b = 0
    else:
        b = b0 + b_coef * s

    if s < 1:
        return None

    # Final verification
    for r in range(4):
        i = perm[r]
        p = PX[r]
        q = PY[r]
        x, y = pts[i]

        tx = a + p * s
        ty = b + q * s

        if (mask >> r) & 1:
            # Horizontal movement
            if ty != y or abs(tx - x) > L:
                return None
        else:
            # Vertical movement
            if tx != x or abs(ty - y) > L:
                return None

    if not construct:
        return s, a, b, None

    targets = [None] * 4
    for r in range(4):
        i = perm[r]
        targets[i] = (a + PX[r] * s, b + PY[r] * s)

    return s, a, b, targets


def exists(L, pts, perms):
    for perm in perms:
        for mask in range(16):
            if solve_case(L, perm, mask, pts, False) is not None:
                return True
    return False


def find_solution(L, pts, perms):
    for perm in perms:
        for mask in range(16):
            res = solve_case(L, perm, mask, pts, True)
            if res is not None:
                return res
    return None


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    perms = list(itertools.permutations(range(4)))

    output = []

    for _ in range(t):
        pts = []
        for _ in range(4):
            x = next(it)
            y = next(it)
            pts.append((x, y))

        if not exists(HIGH, pts, perms):
            output.append("-1")
            continue

        lo = -1
        hi = HIGH

        while hi - lo > 1:
            mid = (lo + hi) // 2
            if exists(mid, pts, perms):
                hi = mid
            else:
                lo = mid

        result = find_solution(hi, pts, perms)
        if result is None:
            output.append("-1")
            continue

        _, _, _, targets = result

        output.append(str(hi))
        for x, y in targets:
            output.append(f"{x} {y}")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()