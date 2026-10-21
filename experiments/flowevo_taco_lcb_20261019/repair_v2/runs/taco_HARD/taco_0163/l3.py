import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    ptr = 1

    ans = [0] * n
    horizontals = []
    verticals = []
    endpoint_h = {}
    endpoint_v = {}

    for i in range(n):
        x1 = data[ptr]
        y1 = data[ptr + 1]
        x2 = data[ptr + 2]
        y2 = data[ptr + 3]
        ptr += 4

        if y1 == y2:  # horizontal
            if x1 < x2:
                xl, xr = x1, x2
            else:
                xl, xr = x2, x1
            y = y1

            horizontals.append((i, y, xl, xr))
            endpoint_h[(xl, y)] = i
            endpoint_h[(xr, y)] = i
        else:  # vertical
            x = x1
            if y1 < y2:
                yb, yt = y1, y2
            else:
                yb, yt = y2, y1

            verticals.append((i, x, yb, yt))
            endpoint_v[(x, yb)] = i
            endpoint_v[(x, yt)] = i

    # Count intersections on every horizontal road.
    if horizontals and verticals:
        ys_vals = [h[1] for h in horizontals]
        ys_vals.extend(v[2] for v in verticals)
        ys_vals.extend(v[3] for v in verticals)

        ys = sorted(set(ys_vals))
        y_id = {y: i + 1 for i, y in enumerate(ys)}
        m = len(ys)

        queries = []
        for hid, y, xl, xr in horizontals:
            yi = y_id[y]
            queries.append((xr, hid, yi, 1))
            queries.append((xl - 1, hid, yi, -1))

        queries.sort()
        verts_sorted = sorted(verticals, key=lambda v: v[1])

        bit = [0] * (m + 2)
        p = 0
        nv = len(verts_sorted)

        for X, hid, yi, sign in queries:
            while p < nv and verts_sorted[p][1] <= X:
                yb = verts_sorted[p][2]
                yt = verts_sorted[p][3]

                left = y_id[yb]
                right = y_id[yt]

                j = left
                while j <= m:
                    bit[j] += 1
                    j += j & -j

                j = right + 1
                while j <= m:
                    bit[j] -= 1
                    j += j & -j

                p += 1

            s = 0
            j = yi
            while j > 0:
                s += bit[j]
                j -= j & -j

            ans[hid] += sign * s

    # Count intersections on every vertical road.
    if horizontals and verticals:
        xs_vals = [v[1] for v in verticals]
        xs_vals.extend(h[2] for h in horizontals)
        xs_vals.extend(h[3] for h in horizontals)

        xs = sorted(set(xs_vals))
        x_id = {x: i + 1 for i, x in enumerate(xs)}
        m2 = len(xs)

        queries2 = []
        for vid, x, yb, yt in verticals:
            xi = x_id[x]
            queries2.append((yt, vid, xi, 1))
            queries2.append((yb - 1, vid, xi, -1))

        queries2.sort()
        horiz_sorted = sorted(horizontals, key=lambda h: h[1])

        bit2 = [0] * (m2 + 2)
        p = 0
        nh = len(horiz_sorted)

        for Y, vid, xi, sign in queries2:
            while p < nh and horiz_sorted[p][1] <= Y:
                xl = horiz_sorted[p][2]
                xr = horiz_sorted[p][3]

                left = x_id[xl]
                right = x_id[xr]

                j = left
                while j <= m2:
                    bit2[j] += 1
                    j += j & -j

                j = right + 1
                while j <= m2:
                    bit2[j] -= 1
                    j += j & -j

                p += 1

            s = 0
            j = xi
            while j > 0:
                s += bit2[j]
                j -= j & -j

            ans[vid] += sign * s

    # Exclude intersections that are endpoints of both roads.
    if endpoint_h and endpoint_v:
        if len(endpoint_h) <= len(endpoint_v):
            for (x, y), hid in endpoint_h.items():
                vid = endpoint_v.get((x, y))
                if vid is not None:
                    ans[hid] -= 1
                    ans[vid] -= 1
        else:
            for (x, y), vid in endpoint_v.items():
                hid = endpoint_h.get((x, y))
                if hid is not None:
                    ans[hid] -= 1
                    ans[vid] -= 1

    total_lights = 0
    for hid, _, _, _ in horizontals:
        total_lights += ans[hid]

    sys.stdout.write(str(total_lights) + "\n")
    sys.stdout.write(" ".join(map(str, ans)) + "\n")


if __name__ == "__main__":
    main()