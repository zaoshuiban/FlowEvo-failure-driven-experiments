import sys
import math
from functools import cmp_to_key


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    raw_points = []
    idx = 1

    for _ in range(n):
        x = data[idx]
        y = data[idx + 1]
        w = data[idx + 2]
        idx += 3
        raw_points.append((x, y, w))

    # Points at the same coordinates can never be separated by a valid line.
    merged = {}
    for x, y, w in raw_points:
        merged[(x, y)] = merged.get((x, y), 0) + w

    points = list(merged.keys())
    weights = [merged[p] for p in points]
    n = len(points)

    total = sum(weights)
    ans = 0

    events = []

    for i in range(n):
        xi, yi = points[i]
        for j in range(i + 1, n):
            xj, yj = points[j]

            dx = xj - xi
            dy = yj - yi

            if dx == 0 and dy == 0:
                continue

            # Normal vector perpendicular to (dx, dy)
            nx = -dy
            ny = dx

            g = math.gcd(abs(nx), abs(ny))
            nx //= g
            ny //= g

            events.append((nx, ny, i, j))
            events.append((-nx, -ny, i, j))

    def half(nx, ny):
        return 0 if (ny > 0 or (ny == 0 and nx >= 0)) else 1

    def angle_cmp(a, b):
        nx1, ny1 = a[0], a[1]
        nx2, ny2 = b[0], b[1]

        h1 = half(nx1, ny1)
        h2 = half(nx2, ny2)

        if h1 != h2:
            return -1 if h1 < h2 else 1

        cross = nx1 * ny2 - ny1 * nx2
        if cross > 0:
            return -1
        if cross < 0:
            return 1
        return 0

    events.sort(key=cmp_to_key(angle_cmp))

    # Initial direction chosen so that no two projections are equal.
    K = 10 ** 18
    start_nx, start_ny = 1, K

    start_pos = 0
    for i, e in enumerate(events):
        nx, ny = e[0], e[1]

        h = half(nx, ny)

        if h > 0:
            start_pos = i
            break

        cross = nx * start_ny - ny * start_nx
        if cross < 0:
            start_pos = i
            break
    else:
        start_pos = 0

    ordered_events = events[start_pos:] + events[:start_pos]

    order = list(range(n))
    order.sort(key=lambda i: points[i][0] * start_nx + points[i][1] * start_ny)

    position = [0] * n
    for i, p in enumerate(order):
        position[p] = i

    def evaluate():
        nonlocal ans

        pref = 0
        for k in range(n + 1):
            if k > 0:
                pref += weights[order[k - 1]]

            other = total - pref
            smaller = pref if pref < other else other

            if smaller > ans:
                ans = smaller

    evaluate()

    m = len(ordered_events)
    group_start = 0

    while group_start < m:
        nx = ordered_events[group_start][0]
        ny = ordered_events[group_start][1]

        group_end = group_start + 1
        while (
            group_end < m
            and ordered_events[group_end][0] == nx
            and ordered_events[group_end][1] == ny
        ):
            group_end += 1

        # All swaps with the same normal direction happen simultaneously.
        for t in range(group_start, group_end):
            _, _, i, j = ordered_events[t]

            pi = position[i]
            pj = position[j]

            order[pi], order[pj] = order[pj], order[pi]
            position[i] = pj
            position[j] = pi

        evaluate()

        group_start = group_end

    print(ans)


if __name__ == "__main__":
    solve()