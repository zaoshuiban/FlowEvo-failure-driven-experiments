import sys


class Fenwick:
    __slots__ = ("n", "bit")

    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 2)

    def add(self, i, delta):
        n = self.n
        bit = self.bit
        while i <= n:
            bit[i] += delta
            i += i & -i

    def query(self, i):
        res = 0
        bit = self.bit
        while i > 0:
            res += bit[i]
            i -= i & -i
        return res


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    pos = 1

    MAXC = 100000
    SIZE = MAXC + 4

    ans = [0] * n

    horizontals = []
    verticals = []

    endpoint_h = {}
    endpoint_v = {}

    for idx in range(n):
        x1 = data[pos]
        y1 = data[pos + 1]
        x2 = data[pos + 2]
        y2 = data[pos + 3]
        pos += 4

        if y1 == y2:
            y = y1
            xl = min(x1, x2)
            xr = max(x1, x2)

            horizontals.append((idx, y, xl, xr))
            endpoint_h[(xl, y)] = idx
            endpoint_h[(xr, y)] = idx
        else:
            x = x1
            yb = min(y1, y2)
            yt = max(y1, y2)

            verticals.append((idx, x, yb, yt))
            endpoint_v[(x, yb)] = idx
            endpoint_v[(x, yt)] = idx

    # Count vertical roads crossing each horizontal road.
    add_by_x = [[] for _ in range(SIZE)]
    query_by_x = [[] for _ in range(SIZE)]

    for idx, x, yb, yt in verticals:
        add_by_x[x].append((yb, yt))

    for idx, y, xl, xr in horizontals:
        query_by_x[xr].append((idx, y, 1))
        query_by_x[xl - 1].append((idx, y, -1))

    bit = Fenwick(MAXC + 2)

    for x in range(MAXC + 2):
        for yb, yt in add_by_x[x]:
            bit.add(yb, 1)
            bit.add(yt + 1, -1)

        for idx, y, sign in query_by_x[x]:
            ans[idx] += sign * bit.query(y)

    del add_by_x, query_by_x, bit

    # Count horizontal roads crossing each vertical road.
    add_by_y = [[] for _ in range(SIZE)]
    query_by_y = [[] for _ in range(SIZE)]

    for idx, y, xl, xr in horizontals:
        add_by_y[y].append((xl, xr))

    for idx, x, yb, yt in verticals:
        query_by_y[yt].append((idx, x, 1))
        query_by_y[yb - 1].append((idx, x, -1))

    bit = Fenwick(MAXC + 2)

    for y in range(MAXC + 2):
        for xl, xr in add_by_y[y]:
            bit.add(xl, 1)
            bit.add(xr + 1, -1)

        for idx, x, sign in query_by_y[y]:
            ans[idx] += sign * bit.query(x)

    # Remove intersections that are endpoints of both roads.
    for (x, y), hid in endpoint_h.items():
        vid = endpoint_v.get((x, y))
        if vid is not None:
            ans[hid] -= 1
            ans[vid] -= 1

    total_lights = 0
    for idx, y, xl, xr in horizontals:
        total_lights += ans[idx]

    sys.stdout.write(str(total_lights) + "\n")
    sys.stdout.write(" ".join(map(str, ans)) + "\n")


if __name__ == "__main__":
    main()