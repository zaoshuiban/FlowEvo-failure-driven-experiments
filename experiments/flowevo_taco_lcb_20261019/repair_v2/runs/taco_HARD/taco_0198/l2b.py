import sys
import math

def clip_polygon(poly, inside, intersect):
    if not poly:
        return []

    result = []
    prev = poly[-1]
    prev_inside = inside(prev)

    for curr in poly:
        curr_inside = inside(curr)

        if curr_inside:
            if not prev_inside:
                result.append(intersect(prev, curr))
            result.append(curr)
        elif prev_inside:
            result.append(intersect(prev, curr))

        prev = curr
        prev_inside = curr_inside

    return result


def intersect_vertical(a, b, x):
    x1, y1 = a
    x2, y2 = b
    t = (x - x1) / (x2 - x1)
    return (x, y1 + t * (y2 - y1))


def intersect_horizontal(a, b, y):
    x1, y1 = a
    x2, y2 = b
    t = (y - y1) / (y2 - y1)
    return (x1 + t * (x2 - x1), y)


def polygon_area(poly):
    area = 0.0
    n = len(poly)

    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        area += x1 * y2 - x2 * y1

    return abs(area) * 0.5


def main():
    w, h, alpha = map(int, sys.stdin.readline().split())

    half_w = w / 2.0
    half_h = h / 2.0

    angle = math.radians(alpha)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    base_vertices = [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h),
    ]

    rotated = []
    for x, y in base_vertices:
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        rotated.append((rx, ry))

    poly = rotated

    poly = clip_polygon(
        poly,
        lambda p: p[0] >= -half_w,
        lambda a, b: intersect_vertical(a, b, -half_w)
    )

    poly = clip_polygon(
        poly,
        lambda p: p[0] <= half_w,
        lambda a, b: intersect_vertical(a, b, half_w)
    )

    poly = clip_polygon(
        poly,
        lambda p: p[1] >= -half_h,
        lambda a, b: intersect_horizontal(a, b, -half_h)
    )

    poly = clip_polygon(
        poly,
        lambda p: p[1] <= half_h,
        lambda a, b: intersect_horizontal(a, b, half_h)
    )

    print(f"{polygon_area(poly):.12f}")


if __name__ == "__main__":
    main()