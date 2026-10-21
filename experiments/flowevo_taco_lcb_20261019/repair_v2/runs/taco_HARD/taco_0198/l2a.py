import sys
import math


def clip_polygon(poly, a, b, c):
    if not poly:
        return []

    result = []
    px, py = poly[-1]
    prev_value = a * px + b * py - c
    prev_inside = prev_value <= 0.0

    for x, y in poly:
        value = a * x + b * y - c
        inside = value <= 0.0

        if inside:
            if not prev_inside:
                t = prev_value / (prev_value - value)
                result.append((px + t * (x - px), py + t * (y - py)))
            result.append((x, y))
        elif prev_inside:
            t = prev_value / (prev_value - value)
            result.append((px + t * (x - px), py + t * (y - py)))

        px, py = x, y
        prev_value = value
        prev_inside = inside

    return result


def main():
    data = sys.stdin.read().strip().split()
    if not data:
        return

    w, h, alpha = map(int, data[:3])

    half_w = w / 2.0
    half_h = h / 2.0

    polygon = [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h),
    ]

    angle = math.radians(alpha)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    # | x * cos_a + y * sin_a | <= w / 2
    polygon = clip_polygon(polygon, cos_a, sin_a, half_w)
    polygon = clip_polygon(polygon, -cos_a, -sin_a, half_w)

    # | -x * sin_a + y * cos_a | <= h / 2
    polygon = clip_polygon(polygon, -sin_a, cos_a, half_h)
    polygon = clip_polygon(polygon, sin_a, -cos_a, half_h)

    area2 = 0.0
    n = len(polygon)

    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1

    area = abs(area2) / 2.0
    print(f"{area:.12f}")


if __name__ == "__main__":
    main()