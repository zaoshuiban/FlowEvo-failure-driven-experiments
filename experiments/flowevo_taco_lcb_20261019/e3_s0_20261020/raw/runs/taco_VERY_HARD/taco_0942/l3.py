import sys
import itertools


def ceil_div(a, b):
    # b > 0, returns ceil(a / b)
    return -((-a) // b)


class Bounds:
    __slots__ = ("low", "high", "exact", "valid")

    def __init__(self, inf):
        self.low = 1
        self.high = inf
        self.exact = None
        self.valid = True

    def add_le(self, a, c):
        # Add constraint: a * s <= c
        if not self.valid:
            return

        if a == 0:
            if c < 0:
                self.valid = False
            return

        if a > 0:
            # s <= floor(c / a)
            self.high = min(self.high, c // a)
        else:
            # s >= ceil(-c / (-a))
            self.low = max(self.low, ceil_div(-c, -a))

    def add_eq(self, a, c):
        # Add constraint: a * s == c. Here a is -1, 0 or 1.
        if not self.valid:
            return

        if a == 0:
            if c != 0:
                self.valid = False
            return

        if a == 1:
            val = c
        else:  # a == -1
            val = -c

        if self.exact is None:
            self.exact = val
        elif self.exact != val:
            self.valid = False

    def add_abs(self, a, const, d):
        # Add constraint: |a * s + const| <= d
        self.add_le(a, d - const)
        self.add_le(-a, d + const)

    def choose(self):
        if not self.valid:
            return None

        if self.exact is not None:
            s = self.exact
            if s < 1 or s < self.low or s > self.high:
                return None
            return s

        if self.low <= self.high:
            return self.low
        return None


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))

    DX = (0, 1, 1, 0)
    DY = (0, 0, 1, 1)

    permutations = list(itertools.permutations(range(4)))
    INF = 10 ** 30
    BIG_D = 10 ** 18

    answers = []

    for _ in range(t):
        pts = []
        for _ in range(4):
            x = int(next(it))
            y = int(next(it))
            pts.append((x, y))

        def find_solution(d):
            for assign in permutations:
                # assign[label] = bot index

                for mask in range(16):
                    V = []  # moves vertically: final x equals original x
                    H = []  # moves horizontally: final y equals original y

                    for k in range(4):
                        bot = assign[k]
                        x, y = pts[bot]
                        dx = DX[k]
                        dy = DY[k]

                        if (mask >> k) & 1:
                            H.append((bot, dx, dy, x, y))
                        else:
                            V.append((bot, dx, dy, x, y))

                    bounds = Bounds(INF)

                    # Constraints for L (left x coordinate)
                    if V:
                        _, dx0, _, x0, _ = V[0]

                        for idx in range(1, len(V)):
                            _, dx, _, x, _ = V[idx]
                            bounds.add_eq(dx - dx0, x - x0)

                        for _, dx, _, x, _ in H:
                            a = dx - dx0
                            const = x0 - x
                            bounds.add_abs(a, const, d)
                    else:
                        # L is free; existence of L satisfying all H costs.
                        for _, dxp, _, xp, _ in H:
                            for _, dxq, _, xq, _ in H:
                                a = dxq - dxp
                                c = xq - xp + 2 * d
                                bounds.add_le(a, c)

                    # Constraints for B (bottom y coordinate)
                    if H:
                        _, _, dy0, _, y0 = H[0]

                        for idx in range(1, len(H)):
                            _, _, dy, _, y = H[idx]
                            bounds.add_eq(dy - dy0, y - y0)

                        for _, _, dy, _, y in V:
                            a = dy - dy0
                            const = y0 - y
                            bounds.add_abs(a, const, d)
                    else:
                        # B is free; existence of B satisfying all V costs.
                        for _, _, dyp, _, yp in V:
                            for _, _, dyq, _, yq in V:
                                a = dyq - dyp
                                c = yq - yp + 2 * d
                                bounds.add_le(a, c)

                    s = bounds.choose()
                    if s is None:
                        continue

                    # Construct L
                    if V:
                        _, dx0, _, x0, _ = V[0]
                        L = x0 - dx0 * s
                    else:
                        low_l = -INF
                        high_l = INF
                        for _, dx, _, x, _ in H:
                            lo = x - dx * s - d
                            hi = x - dx * s + d
                            if lo > low_l:
                                low_l = lo
                            if hi < high_l:
                                high_l = hi

                        if low_l > high_l:
                            continue
                        L = low_l if low_l != -INF else 0

                    # Construct B
                    if H:
                        _, _, dy0, _, y0 = H[0]
                        B = y0 - dy0 * s
                    else:
                        low_b = -INF
                        high_b = INF
                        for _, _, dy, _, y in V:
                            lo = y - dy * s - d
                            hi = y - dy * s + d
                            if lo > low_b:
                                low_b = lo
                            if hi < high_b:
                                high_b = hi

                        if low_b > high_b:
                            continue
                        B = low_b if low_b != -INF else 0

                    positions = [None] * 4

                    for k in range(4):
                        bot = assign[k]
                        positions[bot] = (
                            L + DX[k] * s,
                            B + DY[k] * s
                        )

                    # Safety verification
                    ok = True
                    for i, (x, y) in enumerate(pts):
                        fx, fy = positions[i]

                        if fx == x:
                            cost = abs(fy - y)
                        elif fy == y:
                            cost = abs(fx - x)
                        else:
                            ok = False
                            break

                        if cost > d:
                            ok = False
                            break

                    if ok:
                        return positions, s

            return None

        if find_solution(BIG_D) is None:
            answers.append("-1")
        else:
            lo = -1
            hi = BIG_D

            while hi - lo > 1:
                mid = (lo + hi) // 2
                if find_solution(mid) is not None:
                    hi = mid
                else:
                    lo = mid

            result = find_solution(hi)
            positions, _ = result

            answers.append(str(hi))
            for x, y in positions:
                answers.append(f"{x} {y}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()