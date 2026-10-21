import sys


class Fenwick:
    __slots__ = ("n", "tree")

    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)

    def add(self, i, delta):
        n = self.n
        tree = self.tree
        while i <= n:
            tree[i] += delta
            i += i & -i

    def range_add(self, left, right, delta):
        self.add(left, delta)
        self.add(right + 1, -delta)

    def sum(self, i):
        res = 0
        tree = self.tree
        while i > 0:
            res += tree[i]
            i -= i & -i
        return res


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    pos = 1

    horizontals = []  # (index, x_left, x_right, y)
    verticals = []    # (index, x, y_bottom, y_top)

    max_coord = 0

    for i in range(n):
        x1, y1, x2, y2 = data[pos], data[pos + 1], data[pos + 2], data[pos + 3]
        pos += 4

        max_coord = max(max_coord, x1, y1, x2, y2)

        if x1 == x2:
            if y1 <= y2:
                yl, yr = y1, y2
            else:
                yl, yr = y2, y1
            verticals.append((i, x1, yl, yr))
        else:
            if x1 <= x2:
                xl, xr = x1, x2
            else:
                xl, xr = x2, x1
            horizontals.append((i, xl, xr, y1))

    size = max_coord + 5
    h_count = [0] * n
    v_count = [0] * n

    if horizontals and verticals:
        # Count intersections for every horizontal segment.
        events = []
        for idx, xl, xr, y in horizontals:
            events.append((xr, 1, y, idx))
            events.append((xl - 1, -1, y, idx))

        events.sort(key=lambda e: e[0])
        verticals_sorted = sorted(verticals, key=lambda v: v[1])

        bit = Fenwick(size)
        p = 0
        m = len(verticals_sorted)

        for x, sign, y, idx in events:
            while p < m and verticals_sorted[p][1] <= x:
                _, _, yl, yr = verticals_sorted[p]
                bit.range_add(yl, yr, 1)
                p += 1

            h_count[idx] += sign * bit.sum(y)

        # Count intersections for every vertical segment.
        events = []
        for idx, x, yl, yr in verticals:
            events.append((yr, 1, x, idx))
            events.append((yl - 1, -1, x, idx))

        events.sort(key=lambda e: e[0])
        horizontals_sorted = sorted(horizontals, key=lambda h: h[3])

        bit = Fenwick(size)
        p = 0
        m = len(horizontals_sorted)

        for y, sign, x, idx in events:
            while p < m and horizontals_sorted[p][3] <= y:
                _, xl, xr, _ = horizontals_sorted[p]
                bit.range_add(xl, xr, 1)
                p += 1

            v_count[idx] += sign * bit.sum(x)

        # Remove intersections that are endpoints of both segments.
        h_endpoints = {}
        for idx, xl, xr, y in horizontals:
            h_endpoints[(xl, y)] = idx
            h_endpoints[(xr, y)] = idx

        for idx, x, yl, yr in verticals:
            h_idx = h_endpoints.get((x, yl))
            if h_idx is not None:
                h_count[h_idx] -= 1
                v_count[idx] -= 1

            h_idx = h_endpoints.get((x, yr))
            if h_idx is not None:
                h_count[h_idx] -= 1
                v_count[idx] -= 1

    total = sum(h_count)
    answer = [str(h_count[i] + v_count[i]) for i in range(n)]

    sys.stdout.write(str(total) + "\n" + " ".join(answer) + "\n")


if __name__ == "__main__":
    solve()