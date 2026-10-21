import sys
import math


def clip_polygon(poly, a, b):
    if not poly:
        return []

    ax, ay = a
    bx, by = b
    ex = bx - ax
    ey = by - ay
    eps = 1e-12

    def inside(p):
        px, py = p
        return ex * (py - ay) - ey * (px - ax) >= -eps

    result = []
    n = len(poly)

    for i in range(n):
        cur = poly[i]
        prev = poly[i - 1]

        cur_in = inside(cur)
        prev_in = inside(prev)

        if cur_in:
            if not prev_in:
                dx = cur[0] - prev[0]
                dy = cur[1] - prev[1]
                den = dx * ey - dy * ex

                if abs(den) > 1e-30:
                    num = (ax - prev[0]) * ey - (ay - prev[1]) * ex
                    t = num / den
                    result.append((prev[0] + t * dx, prev[1] + t * dy))
                else:
                    result.append(cur)

            result.append(cur)

        elif prev_in:
            dx = cur[0] - prev[0]
            dy = cur[1] - prev[1]
            den = dx * ey - dy * ex

            if abs(den) > 1e-30:
                num = (ax - prev[0]) * ey - (ay - prev[1]) * ex
                t = num / den
                result.append((prev[0] + t * dx, prev[1] + t * dy))

    return result


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    w, h, alpha = map(int, data[:3])

    if alpha % 180 == 0:
        print(f"{float(w * h):.15f}")
        return

    if alpha == 90:
        c, s = 0.0, 1.0
    else:
        angle = math.radians(alpha)
        c = math.cos(angle)
        s = math.sin(angle)

    a = w / 2.0
    b = h / 2.0

    first = [(-a, -b), (a, -b), (a, b), (-a, b)]

    second = []
    for x, y in first:
        second.append((x * c - y * s, x * s + y * c))

    polygon = first[:]

    for i in range(4):
        polygon = clip_polygon(polygon, second[i], second[(i + 1) % 4])
        if not polygon:
            break

    area = 0.0
    m = len(polygon)

    if m >= 3:
        area2 = 0.0
        for i in range(m):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % m]
            area2 += x1 * y2 - y1 * x2
        area = abs(area2) * 0.5

    print(f"{area:.15f}")


if __name__ == "__main__":
    main()