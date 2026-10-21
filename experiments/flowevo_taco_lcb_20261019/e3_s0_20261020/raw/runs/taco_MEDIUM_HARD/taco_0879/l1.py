import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    x0, y0, ax, ay, bx, by = data[:6]
    xs, ys, t = data[6:9]

    points = []
    x, y = x0, y0
    limit_x = xs + t
    limit_y = ys + t

    while x <= limit_x and y <= limit_y:
        points.append((x, y))
        x = ax * x + bx
        y = ay * y + by

    ans = 0
    n = len(points)

    for i in range(n):
        xi, yi = points[i]
        for j in range(i, n):
            xj, yj = points[j]

            span = (xj - xi) + (yj - yi)
            dist_left = abs(xs - xi) + abs(ys - yi)
            dist_right = abs(xs - xj) + abs(ys - yj)

            if span + min(dist_left, dist_right) <= t:
                ans = max(ans, j - i + 1)

    print(ans)

if __name__ == "__main__":
    main()