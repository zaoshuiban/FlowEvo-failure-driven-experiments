import sys
import math


def main():
    data = sys.stdin.read().strip().split()
    if not data:
        return

    w, h, alpha = map(int, data[:3])

    a = w / 2.0
    b = h / 2.0

    theta = math.radians(alpha)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    # First rectangle, counter-clockwise
    poly = [
        (-a, -b),
        (a, -b),
        (a, b),
        (-a, b)
    ]

    # Second rectangle: rotate the first one around the origin
    rotated = []
    for x, y in poly:
        rotated.append((
            x * cos_t - y * sin_t,
            x * sin_t + y * cos_t
        ))

    def clip(polygon, A, B):
        if not polygon:
            return []

        ax, ay = A
        bx, by = B
        ex = bx - ax
        ey = by - ay

        eps = 1e-10
        result = []

        def inside(p):
            px, py = p
            return ex * (py - ay) - ey * (px - ax) >= -eps

        def intersection(p, q):
            px, py = p
            qx, qy = q

            f0 = ex * (py - ay) - ey * (px - ax)
            f1 = ex * (qy - ay) - ey * (qx - ax)

            den = f0 - f1
            if abs(den) < 1e-30:
                return q

            t = f0 / den
            return (
                px + (qx - px) * t,
                py + (qy - py) * t
            )

        prev = polygon[-1]
        prev_inside = inside(prev)

        for cur in polygon:
            cur_inside = inside(cur)

            if cur_inside:
                if not prev_inside:
                    result.append(intersection(prev, cur))
                result.append(cur)
            elif prev_inside:
                result.append(intersection(prev, cur))

            prev = cur
            prev_inside = cur_inside

        return result

    # Intersect the first rectangle with the second rectangle
    for i in range(4):
        poly = clip(poly, rotated[i], rotated[(i + 1) % 4])
        if not poly:
            break

    if len(poly) < 3:
        area = 0.0
    else:
        twice_area = 0.0
        n = len(poly)

        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            twice_area += x1 * y2 - y1 * x2

        area = abs(twice_area) / 2.0

    print("{:.12f}".format(area))


if __name__ == "__main__":
    main()