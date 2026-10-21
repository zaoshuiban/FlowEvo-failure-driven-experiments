import sys
from itertools import permutations

# All four corners of the unit square: (dx, dy), where corner = (a + dx*s, b + dy*s)
CORNERS = [(0, 0), (0, 1), (1, 0), (1, 1)]
CORNER_PERMS = list(permutations(CORNERS))


def get_form(eqs):
    """
    Equations for one square coordinate v:
        v + c*s = val
    where c is dx or dy in {0,1}.

    Returns:
        None if impossible
        (0, 0, 0)                         for free variable
        (1, val, c)                       if v = val - c*s
        (2, s_value, v_value)             if s and v are fixed
    """
    if not eqs:
        return (0, 0, 0)

    c0, v0 = eqs[0]
    fixed_s = None

    for c, v in eqs[1:]:
        if c != c0:
            # (c - c0) * s = v - v0
            num = v - v0
            den = c - c0
            if num % den != 0:
                return None
            fixed_s = num // den
            break

    if fixed_s is None:
        # All equations have the same coefficient and must also have the same value.
        for c, v in eqs:
            if c != c0 or v != v0:
                return None
        return (1, v0, c0)

    if fixed_s < 1:
        return None

    fixed_v = v0 - c0 * fixed_s

    for c, val in eqs:
        if fixed_v + c * fixed_s != val:
            return None

    return (2, fixed_s, fixed_v)


def feasible_var(form, ineqs, R):
    """
    For one coordinate v, check for which positive integer s the inequalities
        |v + c*s - target| <= R
    can be satisfied.

    Returns an inclusive interval (low, high), where high=None means +infinity,
    or None if impossible.
    """
    typ = form[0]

    if typ == 2:
        s_fixed, v_fixed = form[1], form[2]
        if s_fixed < 1:
            return None
        for c, target in ineqs:
            if abs(v_fixed + c * s_fixed - target) > R:
                return None
        return (s_fixed, s_fixed)

    low = 1
    high = None

    if typ == 0:
        # v is free. Need max lower bound <= min upper bound for every s.
        # For inequalities i and j:
        # target_i - R - c_i*s <= v <= target_i + R - c_i*s
        for c_l, t_l in ineqs:
            for c_u, t_u in ineqs:
                # t_l - R - c_l*s <= t_u + R - c_u*s
                # (c_u - c_l)*s <= t_u - t_l + 2R
                C = t_u - t_l + 2 * R
                d = c_u - c_l

                if d == 0:
                    if C < 0:
                        return None
                elif d == 1:
                    if high is None or C < high:
                        high = C
                else:  # d == -1
                    # -s <= C  =>  s >= -C
                    if -C > low:
                        low = -C

                if high is not None and low > high:
                    return None

        return (low, high)

    if typ == 1:
        # v = value - c_eq*s
        value, c_eq = form[1], form[2]

        for c, target in ineqs:
            A = value - target
            d = c - c_eq

            if d == 0:
                if abs(A) > R:
                    return None
            elif d == 1:
                # -R <= A + s <= R
                l = -R - A
                u = R - A
                if l > low:
                    low = l
                if high is None or u < high:
                    high = u
            else:  # d == -1
                # -R <= A - s <= R
                l = A - R
                u = A + R
                if l > low:
                    low = l
                if high is None or u < high:
                    high = u

            if high is not None and low > high:
                return None

        return (low, high)

    return None


def choose_var(form, ineqs, R, s):
    """Choose a concrete integer value of one square coordinate for fixed s."""
    typ = form[0]

    if typ == 2:
        if s != form[1]:
            return None
        return form[2]

    if typ == 1:
        value, c_eq = form[1], form[2]
        return value - c_eq * s

    if typ == 0:
        if not ineqs:
            return 0

        max_lower = None
        min_upper = None

        for c, target in ineqs:
            low = target - R - c * s
            high = target + R - c * s

            if max_lower is None or low > max_lower:
                max_lower = low
            if min_upper is None or high < min_upper:
                min_upper = high

        if max_lower <= min_upper:
            return max_lower
        return None

    return None


def find_solution(points, R):
    """
    Tries to find final positions for all four bots with maximum movement <= R.
    Returns a list of four final positions in input order, or None.
    """
    for perm in CORNER_PERMS:
        for mask in range(16):
            a_eq = []
            b_eq = []
            a_ineq = []
            b_ineq = []

            for i in range(4):
                dx, dy = perm[i]
                x, y = points[i]

                # bit 1 means: bot is aligned by x, so a + dx*s = x,
                # and it moves vertically. Its y-cost is an inequality on b.
                if (mask >> i) & 1:
                    a_eq.append((dx, x))
                    b_ineq.append((dy, y))
                else:
                    # Aligned by y, so b + dy*s = y,
                    # and it moves horizontally. Its x-cost is an inequality on a.
                    b_eq.append((dy, y))
                    a_ineq.append((dx, x))

            form_a = get_form(a_eq)
            form_b = get_form(b_eq)

            if form_a is None or form_b is None:
                continue

            interval_a = feasible_var(form_a, a_ineq, R)
            interval_b = feasible_var(form_b, b_ineq, R)

            if interval_a is None or interval_b is None:
                continue

            low = max(interval_a[0], interval_b[0], 1)

            high = None
            for h in (interval_a[1], interval_b[1]):
                if h is not None:
                    if high is None or h < high:
                        high = h

            if high is not None and low > high:
                continue

            s = low
            a = choose_var(form_a, a_ineq, R, s)
            b = choose_var(form_b, b_ineq, R, s)

            if a is None or b is None:
                continue

            result = []
            ok = True

            for i in range(4):
                dx, dy = perm[i]
                x, y = points[i]

                qx = a + dx * s
                qy = b + dy * s
                result.append((qx, qy))

                if (mask >> i) & 1:
                    if qx != x or abs(qy - y) > R:
                        ok = False
                        break
                else:
                    if qy != y or abs(qx - x) > R:
                        ok = False
                        break

            if ok:
                return result

    return None


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []
    INF = 10**18

    for _ in range(t):
        points = []
        for _ in range(4):
            x = data[idx]
            y = data[idx + 1]
            idx += 2
            points.append((x, y))

        if find_solution(points, INF) is None:
            output.append("-1")
            continue

        lo = -1
        hi = INF

        while hi - lo > 1:
            mid = (lo + hi) // 2
            if find_solution(points, mid) is not None:
                hi = mid
            else:
                lo = mid

        answer_positions = find_solution(points, hi)

        output.append(str(hi))
        for x, y in answer_positions:
            output.append(f"{x} {y}")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()